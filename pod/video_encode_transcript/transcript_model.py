import numpy as np
import shlex
import subprocess
import json

import os
from timeit import default_timer as timer
import datetime as dt
from datetime import timedelta
import webvtt
from webvtt import WebVTT, Caption
from shlex import quote

import logging

try:
    from ..custom import settings_local
except ImportError:
    from .. import settings as settings_local

from .encoding_utils import sec_to_timestamp

DEBUG = getattr(settings_local, "DEBUG", False)

TRANSCRIPTION_MODEL_PARAM = getattr(settings_local, "TRANSCRIPTION_MODEL_PARAM", False)
USE_TRANSCRIPTION = getattr(settings_local, "USE_TRANSCRIPTION", False)
if USE_TRANSCRIPTION:
    TRANSCRIPTION_TYPE = getattr(settings_local, "TRANSCRIPTION_TYPE", "WHISPER")
    if TRANSCRIPTION_TYPE == "VOSK":
        from vosk import Model, KaldiRecognizer
    elif TRANSCRIPTION_TYPE == "WHISPER":
        import whisper
        from whisper.utils import get_writer

TRANSCRIPTION_NORMALIZE = getattr(settings_local, "TRANSCRIPTION_NORMALIZE", False)
TRANSCRIPTION_NORMALIZE_TARGET_LEVEL = getattr(
    settings_local, "TRANSCRIPTION_NORMALIZE_TARGET_LEVEL", -16.0
)

TRANSCRIPTION_AUDIO_SPLIT_TIME = getattr(
    settings_local, "TRANSCRIPTION_AUDIO_SPLIT_TIME", 600
)  # 10min
# time in sec for phrase length
TRANSCRIPTION_STT_SENTENCE_MAX_LENGTH = getattr(
    settings_local, "TRANSCRIPTION_STT_SENTENCE_MAX_LENGTH", 2
)
TRANSCRIPTION_STT_SENTENCE_BLANK_SPLIT_TIME = getattr(
    settings_local, "TRANSCRIPTION_STT_SENTENCE_BLANK_SPLIT_TIME", 0.5
)
log = logging.getLogger(__name__)


def get_model(lang):
    """Get model for Whisper or Vosk software to transcript audio."""
    transript_model = Model(TRANSCRIPTION_MODEL_PARAM[TRANSCRIPTION_TYPE][lang]["model"])
    return transript_model


def start_transcripting(mp3filepath, duration, lang):
    """
    Start direct transcription.

    Normalize the audio if set, get the model according to the lang and start transcript.
    """
    if TRANSCRIPTION_NORMALIZE:
        mp3filepath = normalize_mp3(mp3filepath)
    if TRANSCRIPTION_TYPE == "WHISPER":
        msg, webvtt, all_text = main_whisper_transcript(mp3filepath, duration, lang)
    else:
        transript_model = get_model(lang)
        msg, webvtt, all_text = start_main_transcript(
            mp3filepath, duration, transript_model
        )
    if DEBUG:
        print(msg)
        print(webvtt)
        print("\n%s\n" % all_text)

    return msg, webvtt


def start_main_transcript(mp3filepath, duration, transript_model):
    """Call transcription depending software type."""
    if TRANSCRIPTION_TYPE == "VOSK":
        msg, webvtt, all_text = main_vosk_transcript(
            mp3filepath, duration, transript_model
        )
    return msg, webvtt, all_text


def convert_samplerate(audio_path, desired_sample_rate, trim_start, duration):
    """Convert audio to subaudio and add good sample rate."""
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

    if TRANSCRIPTION_TYPE == "WHISPER":
        return np.frombuffer(output, np.int16).flatten().astype(np.float32) / 32768.0
    else:
        return np.frombuffer(output, np.int16)


def normalize_mp3(mp3filepath):
    """Normalize the audio to good format and sound level."""
    filename, file_extension = os.path.splitext(mp3filepath)
    mp3normfile = "{}{}{}".format(filename, "_norm", file_extension)
    normalize_cmd = "ffmpeg-normalize {} ".format(quote(mp3filepath))
    normalize_cmd += "-c:a libmp3lame -b:a 192k --normalization-type ebu "
    # normalize_cmd += \
    # '--loudness-range-target 7.0 --true-peak 0.0 --offset 0.0 '
    normalize_cmd += "--target-level {} -f -o {}".format(
        TRANSCRIPTION_NORMALIZE_TARGET_LEVEL, quote(mp3normfile)
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
# TRANSCRIPT VIDEO: MAIN FUNCTION
# #################################


def convert_vosk_samplerate(audio_path, desired_sample_rate, trim_start, duration):
    """Convert audio to the good sample rate."""
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
    """Get subsound from audio and add transcription to result parameter."""
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
    """Convert word and time to webvtt captions."""
    # Function retained because it could be used with the Vosk model
    # (initially used with the old STT model).
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
        # word: <class 'dict'> {'word': 'bonjour', 'start ':
        # 0.58, 'duration': 7.34}
        text_caption.append(word["word"])
        if not (
            (((word[start_key]) - start_caption) < TRANSCRIPTION_STT_SENTENCE_MAX_LENGTH)
            and (
                next_word is not None
                and (blank_duration < TRANSCRIPTION_STT_SENTENCE_BLANK_SPLIT_TIME)
            )
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
                sec_to_timestamp(start_caption),
                sec_to_timestamp(stop_caption),
                " ".join(text_caption),
            )

            webvtt.captions.append(caption)
            # on remet tout à zero pour la prochaine phrase
            start_caption = word[start_key]
            text_caption = []
            last_word_added = word["word"]
    if start_trim + TRANSCRIPTION_AUDIO_SPLIT_TIME > duration:
        # on ajoute ici la dernière phrase de la vidéo
        stop_caption = start_trim + words[-1][start_key] + last_word_duration
        caption = Caption(
            sec_to_timestamp(start_caption),
            sec_to_timestamp(stop_caption),
            " ".join(text_caption),
        )
        webvtt.captions.append(caption)
    return all_text, webvtt


def main_vosk_transcript(norm_mp3_file, duration, transript_model):
    """Vosk transcription."""
    msg = ""
    inference_start = timer()
    msg += "\nInference start %0.3fs." % inference_start
    desired_sample_rate = 16000

    rec = KaldiRecognizer(transript_model, desired_sample_rate)
    rec.SetWords(True)

    webvtt = WebVTT()
    all_text = ""
    for start_trim in range(0, duration, TRANSCRIPTION_AUDIO_SPLIT_TIME):
        audio = convert_vosk_samplerate(
            norm_mp3_file,
            desired_sample_rate,
            start_trim,
            TRANSCRIPTION_AUDIO_SPLIT_TIME,  # dur
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
                sec_to_timestamp(start_caption),
                sec_to_timestamp(stop_caption),
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


def main_whisper_transcript(norm_mp3_file, duration, lang):
    """Whisper transcription."""
    msg = ""
    all_text = ""
    inference_start = timer()
    desired_sample_rate = 16000
    msg += "\nInference start %0.3fs." % inference_start

    model = whisper.load_model(
        TRANSCRIPTION_MODEL_PARAM[TRANSCRIPTION_TYPE][lang]["model"],
        download_root=TRANSCRIPTION_MODEL_PARAM[TRANSCRIPTION_TYPE][lang][
            "download_root"
        ],
    )
    audio = convert_samplerate(norm_mp3_file, desired_sample_rate, 0, duration)
    transcription = model.transcribe(
        audio, language=lang, initial_prompt="prompt", word_timestamps=True
    )
    dirname = os.path.dirname(norm_mp3_file)
    filename = os.path.basename(norm_mp3_file).replace(".mp3", ".vtt")
    vtt_writer = get_writer("vtt", dirname)
    word_options = {"highlight_words": False, "max_line_count": 2, "max_line_width": 40}
    vtt_writer(transcription, filename, word_options)
    wvtt = webvtt.read(os.path.join(dirname, filename))
    inference_end = timer() - inference_start
    msg += "\nInference took %0.3fs." % inference_end
    return msg, wvtt, all_text


def change_previous_end_caption(webvtt, start_caption):
    """Change the end time for caption."""
    if len(webvtt.captions) > 0:
        prev_end = dt.datetime.strptime(webvtt.captions[-1].end, "%H:%M:%S.%f")
        td_prev_end = timedelta(
            hours=prev_end.hour,
            minutes=prev_end.minute,
            seconds=prev_end.second,
            microseconds=prev_end.microsecond,
        ).total_seconds()
        if td_prev_end > start_caption:
            webvtt.captions[-1].end = sec_to_timestamp(start_caption)


def get_text_caption(text_caption, last_word_added):
    """Get the text for a caption."""
    try:
        first_index = text_caption.index(last_word_added)
        return text_caption[first_index + 1 :]
    except ValueError:
        return text_caption


def words_from_candidate_transcript(metadata):
    """Get words list from transcription."""
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
