from django.conf import settings
from django.core.files import File
from pod.completion.models import Track
from pod.main.tasks import task_start_transcript

from .utils import change_encoding_step, add_encoding_log
from .utils import send_email, send_email_transcript
from .models import Video

import numpy as np
import shlex
import subprocess
import json

import sys
import os
import time
from timeit import default_timer as timer
import datetime as dt
from datetime import timedelta

from webvtt import WebVTT, Caption
from tempfile import NamedTemporaryFile

try:
    from shhlex import quote
except ImportError:
    from pipes import quote

import threading
import logging

MODEL_PARAM = getattr(settings, "MODEL_PARAM", False)
TRANSCRIPT = getattr(settings, "USE_TRANSCRIPTION", False)
if TRANSCRIPT:
    TRANSCRIPTION_TYPE = getattr(settings, "TRANSCRIPTION_TYPE", "STT")
    if TRANSCRIPTION_TYPE == "VOSK":
        from vosk import Model, KaldiRecognizer
    elif TRANSCRIPTION_TYPE == "STT":
        from stt import Model

DEBUG = getattr(settings, "DEBUG", False)

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder

    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel

STT_PARAM = getattr(settings, "STT_PARAM", dict())
AUDIO_SPLIT_TIME = getattr(settings, "AUDIO_SPLIT_TIME", 600)  # 10min
# time in sec for phrase length
SENTENCE_MAX_LENGTH = getattr(settings, "SENTENCE_MAX_LENGTH", 3)
SENTENCE_BLANK_SPLIT_TIME = getattr(settings, "SENTENCE_BLANK_SPLIT_TIME", 0.5)
WORDS_PER_LINE = getattr(settings, "WORDS_PER_LINE", 7)

NORMALIZE = getattr(settings, "NORMALIZE", False)
NORMALIZE_TARGET_LEVEL = getattr(settings, "NORMALIZE_TARGET_LEVEL", -16.0)

EMAIL_ON_TRANSCRIPTING_COMPLETION = getattr(
    settings, "EMAIL_ON_TRANSCRIPTING_COMPLETION", True
)

CELERY_TO_ENCODE = getattr(settings, "CELERY_TO_ENCODE", False)

log = logging.getLogger(__name__)

"""
TO TEST IN THE SHELL -->
from pod.video.transcript import *
stt_model = get_model("fr")
msg, webvtt, all_text = main_stt_transcript(
    "/test/audio_192k_pod.mp3", # file
    177, # file duration
    stt_model # model stt loaded
)
print(webvtt)
"""

# ##########################################################################
# TRANSCRIPT VIDEO: THREAD TO LAUNCH TRANSCRIPT
# ##########################################################################


def start_remote_transcript(video_id, threaded=True):
    # load module here to prevent circular import
    from .remote_transcript import remote_transcript_video

    if threaded:
        log.info("START ENCODE VIDEO ID %s" % video_id)
        t = threading.Thread(target=remote_transcript_video, args=[video_id])
        t.setDaemon(True)
        t.start()
    else:
        remote_transcript_video(video_id)


def start_transcript(video_id, threaded=True):
    if threaded:
        if CELERY_TO_ENCODE:
            task_start_transcript.delay(video_id)
        else:
            log.info("START TRANSCRIPT VIDEO %s" % video_id)
            t = threading.Thread(target=main_threaded_transcript, args=[video_id])
            t.setDaemon(True)
            t.start()
    else:
        main_threaded_transcript(video_id)


def get_model(lang):
    transript_model = Model(MODEL_PARAM[TRANSCRIPTION_TYPE][lang]["model"])
    if TRANSCRIPTION_TYPE == "STT":
        if MODEL_PARAM[TRANSCRIPTION_TYPE][lang].get("beam_width"):
            transript_model.setBeamWidth(
                MODEL_PARAM[TRANSCRIPTION_TYPE][lang]["beam_width"]
            )
        if MODEL_PARAM[TRANSCRIPTION_TYPE][lang].get("scorer"):
            print(
                "Loading scorer from files {}".format(
                    MODEL_PARAM[TRANSCRIPTION_TYPE][lang]["scorer"]
                ),
                file=sys.stderr,
            )
            scorer_load_start = timer()
            transript_model.enableExternalScorer(
                MODEL_PARAM[TRANSCRIPTION_TYPE][lang]["scorer"]
            )
            scorer_load_end = timer() - scorer_load_start
            print("Loaded scorer in {:.3}s.".format(scorer_load_end), file=sys.stderr)
            if MODEL_PARAM[TRANSCRIPTION_TYPE][lang].get("lm_alpha") and MODEL_PARAM[
                TRANSCRIPTION_TYPE
            ][lang].get("lm_beta"):
                transript_model.setScorerAlphaBeta(
                    MODEL_PARAM[TRANSCRIPTION_TYPE][lang]["lm_alpha"],
                    MODEL_PARAM[TRANSCRIPTION_TYPE][lang]["lm_beta"],
                )
    return transript_model


def start_main_transcript(mp3filepath, video_to_encode, transript_model):
    if TRANSCRIPTION_TYPE == "STT":
        msg, webvtt, all_text = main_stt_transcript(
            mp3filepath, video_to_encode.duration, transript_model
        )
    elif TRANSCRIPTION_TYPE == "VOSK":
        msg, webvtt, all_text = main_vosk_transcript(
            mp3filepath, video_to_encode.duration, transript_model
        )
    return msg, webvtt, all_text


def main_threaded_transcript(video_to_encode_id):

    change_encoding_step(video_to_encode_id, 5, "transcripting audio")

    video_to_encode = Video.objects.get(id=video_to_encode_id)

    msg = ""
    lang = video_to_encode.main_lang
    # check if MODEL_PARAM [lang] exist
    if not MODEL_PARAM[TRANSCRIPTION_TYPE].get(lang):
        msg += "\n no stt model found for lang:%s." % lang
        msg += "Please add it in MODEL_PARAM."
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
    else:
        transript_model = get_model(lang)

        mp3file = (
            video_to_encode.get_video_mp3().source_file
            if video_to_encode.get_video_mp3()
            else None
        )
        if mp3file is None:
            msg += "\n no mp3 file found for video :%s." % video_to_encode.id
            change_encoding_step(video_to_encode.id, -1, msg)
            send_email(msg, video_to_encode.id)
        else:
            # NORMALIZE MP3
            mp3filepath = mp3file.path
            if NORMALIZE:
                mp3filepath = normalize_mp3(mp3filepath)

            msg, webvtt, all_text = start_main_transcript(
                mp3filepath, video_to_encode, transript_model
            )
            if DEBUG:
                print(msg)
                print(webvtt)
                print("\n%s\n" % all_text)
            msg += saveVTT(video_to_encode, webvtt)
            change_encoding_step(video_to_encode.id, 0, "done")
            # envois mail fin transcription
            if EMAIL_ON_TRANSCRIPTING_COMPLETION:
                send_email_transcript(video_to_encode)

    add_encoding_log(video_to_encode.id, msg)


def convert_samplerate(audio_path, desired_sample_rate, trim_start, duration):
    sox_cmd = "sox {} --type raw --bits 16 --channels 1 --rate {} ".format(
        quote(audio_path), desired_sample_rate
    )
    sox_cmd += "--encoding signed-integer --endian little --compression 0.0 "
    sox_cmd += "--no-dither - trim {} {}".format(trim_start, duration)

    try:
        output = subprocess.check_output(shlex.split(sox_cmd), stderr=subprocess.PIPE)

    except subprocess.CalledProcessError as e:
        raise RuntimeError("SoX returned non-zero status: {}".format(e.stderr))
    except OSError as e:
        raise OSError(
            e.errno,
            "SoX not found, use {}hz files or install it: {}".format(
                desired_sample_rate, e.strerror
            ),
        )

    return np.frombuffer(output, np.int16)


def normalize_mp3(mp3filepath):
    filename, file_extension = os.path.splitext(mp3filepath)
    mp3normfile = "{}{}{}".format(filename, "_norm", file_extension)
    normalize_cmd = "ffmpeg-normalize {} ".format(quote(mp3filepath))
    normalize_cmd += "-c:a libmp3lame -b:a 192k --normalization-type ebu "
    # normalize_cmd += \
    # '--loudness-range-target 7.0 --true-peak 0.0 --offset 0.0 '
    normalize_cmd += "--target-level {} -f -o {}".format(
        NORMALIZE_TARGET_LEVEL, quote(mp3normfile)
    )
    if DEBUG:
        print(normalize_cmd)
    try:
        subprocess.check_output(shlex.split(normalize_cmd), stderr=subprocess.PIPE)
        return mp3normfile
    except subprocess.CalledProcessError as e:
        log.error("ffmpeg-normalize returned non-zero status: {}".format(e.stderr))
        return mp3filepath
    except OSError as e:
        log.error("ffmpeg-normalize not found {}".format(e.strerror))
        return mp3filepath


# #################################
# TRANSCRIPT VIDEO : MAIN FUNCTION
# #################################


def convert_vosk_samplerate(audio_path, desired_sample_rate, trim_start, duration):
    sox_cmd = "sox {} --type raw --bits 16 --channels 1 --rate {} ".format(
        quote(audio_path), desired_sample_rate
    )
    sox_cmd += "--encoding signed-integer --endian little --compression 0.0 "
    sox_cmd += "--no-dither - trim {} {}".format(trim_start, duration)

    try:
        output = subprocess.Popen(shlex.split(sox_cmd), stdout=subprocess.PIPE)

    except subprocess.CalledProcessError as e:
        raise RuntimeError("SoX returned non-zero status: {}".format(e.stderr))
    except OSError as e:
        raise OSError(
            e.errno,
            "SoX not found, use {}hz files or install it: {}".format(
                desired_sample_rate, e.strerror
            ),
        )
    return output


def get_word_result_from_data(results, audio, rec):
    while True:
        data = audio.stdout.read(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            results.append(rec.Result())
    results.append(rec.Result())


def words_to_vtt(
    words,
    start_trim,
    duration,
    is_first_caption,
    text_caption,
    start_caption,
    last_word_added,
    all_text,
    webvtt,
):
    for index, word in enumerate(words):
        start_key = "start_time"
        word_duration = word.get("duration", 0)
        last_word = words[-1]
        last_word_duration = last_word.get("duration", 0)
        if TRANSCRIPTION_TYPE == "VOSK":
            start_key = "start"
            word_duration = word["end"] - word["start"]
            last_word_duration = words[-1]["end"] - words[-1]["start"]
        next_word = None
        blank_duration = 0
        if word != words[-1] and (index + 1) < len(words):
            next_word = words[index + 1]
            blank_duration = ((next_word[start_key]) - start_caption) - (
                ((word[start_key]) - start_caption) + word_duration
            )
        all_text += word["word"] + " "
        # word : <class 'dict'> {'word': 'bonjour', 'start ':
        # 0.58, 'duration': 7.34}
        text_caption.append(word["word"])
        if not (
            (((word[start_key]) - start_caption) < SENTENCE_MAX_LENGTH)
            and (next_word is not None and (blank_duration < SENTENCE_BLANK_SPLIT_TIME))
        ):
            # on créé le caption
            if is_first_caption:
                # A revoir, fusion de la nouvelle ligne avec
                # l'ancienne...
                is_first_caption = False
                text_caption = get_text_caption(text_caption, last_word_added)

            stop_caption = word[start_key] + word_duration

            # on evite le chevauchement
            change_previous_end_caption(webvtt, start_caption)

            caption = Caption(
                format_time_caption(start_caption),
                format_time_caption(stop_caption),
                " ".join(text_caption),
            )

            webvtt.captions.append(caption)
            # on remet tout à zero pour la prochaine phrase
            start_caption = word[start_key]
            text_caption = []
            last_word_added = word["word"]
    if start_trim + AUDIO_SPLIT_TIME > duration:
        # on ajoute ici la dernière phrase de la vidéo
        stop_caption = start_trim + words[-1][start_key] + last_word_duration
        caption = Caption(
            format_time_caption(start_caption),
            format_time_caption(stop_caption),
            " ".join(text_caption),
        )
        webvtt.captions.append(caption)
    return all_text, webvtt


def main_vosk_transcript(norm_mp3_file, duration, transript_model):
    msg = ""
    inference_start = timer()
    msg += "\nInference start %0.3fs." % inference_start
    desired_sample_rate = 16000

    rec = KaldiRecognizer(transript_model, desired_sample_rate)
    rec.SetWords(True)

    webvtt = WebVTT()
    all_text = ""
    for start_trim in range(0, duration, AUDIO_SPLIT_TIME):
        audio = convert_vosk_samplerate(
            norm_mp3_file, desired_sample_rate, start_trim, AUDIO_SPLIT_TIME  # dur
        )
        msg += "\nRunning inference."
        results = []
        get_word_result_from_data(results, audio, rec)
        for res in results:
            words = json.loads(res).get("result")
            text = json.loads(res).get("text")
            if not words:
                continue
            start_caption = words[0]["start"]
            stop_caption = words[-1]["end"]
            caption = Caption(
                format_time_caption(start_caption),
                format_time_caption(stop_caption),
                text,
            )
            webvtt.captions.append(caption)
            """
            text_caption = []
            is_first_caption = True
            all_text, webvtt = words_to_vtt(
                words,
                start_trim,
                duration,
                is_first_caption,
                text_caption,
                start_caption,
                last_word_added,
                all_text,
                webvtt,
            )
            """
    inference_end = timer() - inference_start

    msg += "\nInference took %0.3fs." % inference_end
    return msg, webvtt, all_text


def main_stt_transcript(norm_mp3_file, duration, transript_model):
    msg = ""
    inference_start = timer()
    msg += "\nInference start %0.3fs." % inference_start

    desired_sample_rate = transript_model.sampleRate()

    webvtt = WebVTT()

    last_word_added = ""
    metadata = None

    all_text = ""

    for start_trim in range(0, duration, AUDIO_SPLIT_TIME):

        end_trim = (
            duration
            if start_trim + AUDIO_SPLIT_TIME > duration
            else (start_trim + AUDIO_SPLIT_TIME + SENTENCE_MAX_LENGTH)
        )

        dur = (
            (AUDIO_SPLIT_TIME + SENTENCE_MAX_LENGTH)
            if start_trim + AUDIO_SPLIT_TIME + SENTENCE_MAX_LENGTH < duration
            else (duration - start_trim)
        )

        msg += "\ntake audio from %s to %s - %s" % (start_trim, end_trim, dur)

        audio = convert_samplerate(norm_mp3_file, desired_sample_rate, start_trim, dur)
        msg += "\nRunning inference."

        metadata = transript_model.sttWithMetadata(audio)

        for transcript in metadata.transcripts:
            msg += "\nConfidence : %s" % transcript.confidence
            words = words_from_candidate_transcript(transcript)
            start_caption = start_trim + words[0]["start_time"]
            text_caption = []
            is_first_caption = True
            all_text, webvtt = words_to_vtt(
                words,
                start_trim,
                duration,
                is_first_caption,
                text_caption,
                start_caption,
                last_word_added,
                all_text,
                webvtt,
            )
    inference_end = timer() - inference_start

    msg += "\nInference took %0.3fs." % inference_end
    return msg, webvtt, all_text


def change_previous_end_caption(webvtt, start_caption):
    if len(webvtt.captions) > 0:
        prev_end = dt.datetime.strptime(webvtt.captions[-1].end, "%H:%M:%S.%f")
        td_prev_end = timedelta(
            hours=prev_end.hour,
            minutes=prev_end.minute,
            seconds=prev_end.second,
            microseconds=prev_end.microsecond,
        ).total_seconds()
        if td_prev_end > start_caption:
            webvtt.captions[-1].end = format_time_caption(start_caption)


def format_time_caption(time_caption):
    return (
        dt.datetime.utcfromtimestamp(0) + timedelta(seconds=float(time_caption))
    ).strftime("%H:%M:%S.%f")[:-3]


def get_text_caption(text_caption, last_word_added):
    try:
        first_index = text_caption.index(last_word_added)
        return text_caption[first_index + 1 :]
    except ValueError:
        return text_caption


def words_from_candidate_transcript(metadata):
    word = ""
    word_list = []
    word_start_time = 0
    # Loop through each character
    for i, token in enumerate(metadata.tokens):
        # Append character to word if it's not a space
        if token.text != " ":
            if len(word) == 0:
                # Log the start time of the new word
                word_start_time = token.start_time

            word = word + token.text
        # Word boundary is either a space or the last character in the array
        if token.text == " " or i == len(metadata.tokens) - 1:
            word_duration = token.start_time - word_start_time

            if word_duration < 0:
                word_duration = 0

            each_word = dict()
            each_word["word"] = word
            each_word["start_time"] = round(word_start_time, 4)
            each_word["duration"] = round(word_duration, 4)

            word_list.append(each_word)
            # Reset
            word = ""
            word_start_time = 0

    return word_list


def saveVTT(video, webvtt):
    msg = "\nSAVE TRANSCRIPT WEBVTT : %s" % time.ctime()
    lang = video.main_lang
    temp_vtt_file = NamedTemporaryFile(suffix=".vtt")
    webvtt.save(temp_vtt_file.name)
    if webvtt.captions:
        msg += "\nstore vtt file in bdd with CustomFileModel model file field"
        if FILEPICKER:
            videodir, created = UserFolder.objects.get_or_create(
                name="%s" % video.slug, owner=video.owner
            )
            """
            previousSubtitleFile = CustomFileModel.objects.filter(
                name__startswith="subtitle_%s" % lang,
                folder=videodir,
                created_by=video.owner
            )
            """
            # for subt in previousSubtitleFile:
            #     subt.delete()
            subtitleFile, created = CustomFileModel.objects.get_or_create(
                name="subtitle_%s_%s" % (lang, time.strftime("%Y%m%d-%H%M%S")),
                folder=videodir,
                created_by=video.owner,
            )
            if subtitleFile.file and os.path.isfile(subtitleFile.file.path):
                os.remove(subtitleFile.file.path)
        else:
            subtitleFile, created = CustomFileModel.objects.get_or_create()

        subtitleFile.file.save(
            "subtitle_%s_%s.vtt" % (lang, time.strftime("%Y%m%d-%H%M%S")),
            File(temp_vtt_file),
        )
        msg += "\nstore vtt file in bdd with Track model src field"

        subtitleVtt, created = Track.objects.get_or_create(video=video, lang=lang)
        subtitleVtt.src = subtitleFile
        subtitleVtt.lang = lang
        subtitleVtt.save()
    else:
        msg += "\nERROR SUBTITLES Output size is 0"
    return msg
