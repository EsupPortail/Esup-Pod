from django.conf import settings
from django.core.files import File
from pod.completion.models import Track

from .utils import change_encoding_step, add_encoding_log
from .utils import send_email, send_email_transcript
from .models import Video

import numpy as np
import shlex
import subprocess
# import sys
import os
import time
from timeit import default_timer as timer
from datetime import timedelta

from webvtt import WebVTT, Caption
from tempfile import NamedTemporaryFile

try:
    from shhlex import quote
except ImportError:
    from pipes import quote

import threading
import logging

TRANSCRIPT = getattr(settings, 'USE_TRANSCRIPTION', False)
if TRANSCRIPT:
    from deepspeech import Model

DEBUG = getattr(settings, 'DEBUG', False)

if getattr(settings, 'USE_PODFILE', False):
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder
    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel

DS_PARAM = getattr(settings, 'DS_PARAM', dict())
AUDIO_SPLIT_TIME = getattr(settings, 'AUDIO_SPLIT_TIME', 300)  # 5min
# time in sec for phrase length
SENTENCE_MAX_LENGTH = getattr(settings, 'SENTENCE_MAX_LENGTH', 3)

NORMALIZE_TARGET_LEVEL = getattr(settings, 'NORMALIZE_TARGET_LEVEL', -16.0)

EMAIL_ON_TRANSCRIPTING_COMPLETION = getattr(
    settings, 'EMAIL_ON_TRANSCRIPTING_COMPLETION', True)

log = logging.getLogger(__name__)


def start_transcript(video_id):
    log.info("START TRANSCRIPT VIDEO %s" % video_id)
    t = threading.Thread(target=main_threaded_transcript,
                         args=[video_id])
    t.setDaemon(True)
    t.start()


def main_threaded_transcript(video_to_encode_id):

    change_encoding_step(
        video_to_encode_id, 5,
        "transcripting audio")

    video_to_encode = Video.objects.get(id=video_to_encode_id)

    msg = ''
    lang = video_to_encode.main_lang
    # check if DS_PARAM [lang] exist
    if not DS_PARAM.get(lang):
        msg += "\n no deepspeech model found for lang:%s." % lang
        msg += "Please add it in DS_PARAM."
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
    else:
        ds_model = Model(
            DS_PARAM[lang]['model'], DS_PARAM[lang]['beam_width']
        )
        if all([cond in DS_PARAM[lang]
                for cond in ['alphabet', 'lm', 'trie',
                             'lm_alpha', 'lm_beta']]):
            ds_model.enableDecoderWithLM(
                DS_PARAM[lang]['lm'], DS_PARAM[lang]['trie'],
                DS_PARAM[lang]['lm_alpha'], DS_PARAM[lang]['lm_beta']
            )
        msg = main_transcript(video_to_encode, ds_model)

    add_encoding_log(video_to_encode.id, msg)


def convert_samplerate(audio_path, desired_sample_rate, trim_start, duration):
    sox_cmd = 'sox {} --type raw --bits 16 --channels 1 --rate {} '.format(
        quote(audio_path), desired_sample_rate)
    sox_cmd += '--encoding signed-integer --endian little --compression 0.0 '
    sox_cmd += '--no-dither - trim {} {}'.format(trim_start, duration)

    try:
        output = subprocess.check_output(
            shlex.split(sox_cmd), stderr=subprocess.PIPE)

    except subprocess.CalledProcessError as e:
        raise RuntimeError('SoX returned non-zero status: {}'.format(e.stderr))
    except OSError as e:
        raise OSError(e.errno,
                      'SoX not found, use {}hz files or install it: {}'.format(
                          desired_sample_rate, e.strerror))

    return np.frombuffer(output, np.int16)


def normalize_mp3(mp3filepath):
    filename, file_extension = os.path.splitext(mp3filepath)
    mp3normfile = '{}{}{}'.format(filename, '_norm', file_extension)
    normalize_cmd = 'ffmpeg-normalize {} '.format(quote(mp3filepath))
    normalize_cmd += '-c:a libmp3lame -b:a 192k --normalization-type ebu '
    # normalize_cmd += \
    # '--loudness-range-target 7.0 --true-peak 0.0 --offset 0.0 '
    normalize_cmd += '--target-level {} -f -o {}'.format(
        NORMALIZE_TARGET_LEVEL, quote(mp3normfile))
    if DEBUG:
        print(normalize_cmd)
    try:
        subprocess.check_output(
            shlex.split(normalize_cmd), stderr=subprocess.PIPE)
        return mp3normfile
    except subprocess.CalledProcessError as e:
        log.error('ffmpeg-normalize returned non-zero status: {}'.format(
            e.stderr))
        return mp3filepath
    except OSError as e:
        log.error('ffmpeg-normalize not found {}'.format(e.strerror))
        return mp3filepath

# #################################
# TRANSCRIPT VIDEO : MAIN FUNCTION
# #################################


def main_transcript(video_to_encode, ds_model):
    msg = ""
    inference_start = timer()
    msg += '\nInference start %0.3fs.' % inference_start

    mp3file = video_to_encode.get_video_mp3(
    ).source_file if video_to_encode.get_video_mp3() else None
    if mp3file is None:
        msg += "\n no mp3 file found for video :%s." % video_to_encode.id
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
        return msg

    # NORMALIZE mp3file
    norm_mp3_file = normalize_mp3(mp3file.path)

    desired_sample_rate = ds_model.sampleRate()

    webvtt = WebVTT()

    last_item = None
    sentences = []
    sentence = []
    metadata = None

    for start_trim in range(0, video_to_encode.duration, AUDIO_SPLIT_TIME):

        end_trim = video_to_encode.duration if start_trim + \
            AUDIO_SPLIT_TIME > video_to_encode.duration else (
                start_trim + AUDIO_SPLIT_TIME + SENTENCE_MAX_LENGTH)

        duration = (AUDIO_SPLIT_TIME + SENTENCE_MAX_LENGTH) if start_trim + \
            AUDIO_SPLIT_TIME + SENTENCE_MAX_LENGTH < video_to_encode.duration \
            else (video_to_encode.duration - start_trim)

        msg += "\ntake audio from %s to %s - %s" % (
            start_trim, end_trim, duration)

        audio = convert_samplerate(
            norm_mp3_file, desired_sample_rate, start_trim, duration)
        msg += '\nRunning inference.'

        metadata = ds_model.sttWithMetadata(audio)

        msg += '\nConfidence : %s' % metadata.confidence

        sentences[:] = []  # empty list
        sentence[:] = []  # empty list

        if len(metadata.items) > 0:
            refItem = metadata.items[0]
            index = get_index(metadata, last_item,
                              start_trim) if last_item else 0
            # nb of character in AUDIO_SPLIT_TIME
            msg += "METADATA ITEMS : %d " % len(metadata.items)
            sentences = get_sentences(metadata, refItem, index)
            last_item = (
                sentences[-1][-1].character, sentences[-1][-1].start_time
            ) if len(sentences) > 0 else ()
            for sent in sentences:
                if len(sent) > 0:
                    start_time = sent[0].start_time + start_trim
                    end_time = sent[-1].start_time + start_trim
                    str_sentence = ''.join(item.character for item in sent)
                    # print(start_time, end_time, str_sentence)
                    caption = Caption(
                        '%s.%s' % (timedelta(
                            seconds=int(str(start_time).split('.')[0])),
                            str('%.3f' % start_time).split('.')[1]),
                        '%s.%s' % (timedelta(
                            seconds=int(str(end_time).split('.')[0])),
                            str('%.3f' % end_time).split('.')[1]),
                        ['%s' % str_sentence]
                    )
                    webvtt.captions.append(caption)
    # print(webvtt)
    msg += saveVTT(video_to_encode, webvtt)
    inference_end = timer() - inference_start
    msg += '\nInference took %0.3fs.' % inference_end
    # print(msg)
    change_encoding_step(video_to_encode.id, 0, "done")
    # envois mail fin transcription
    if EMAIL_ON_TRANSCRIPTING_COMPLETION:
        send_email_transcript(video_to_encode)
    return msg


def get_sentences(metadata, refItem, index):
    sentence = []
    sentences = []
    for item in metadata.items[index:]:
        if((item.start_time - refItem.start_time) < SENTENCE_MAX_LENGTH):
            sentence.append(item)
        else:
            if item.character == ' ':
                sentences.append(sentence)
                sentence = []
                refItem = item
            else:
                sentence.append(item)
    if sentence != []:
        sentences.append(sentence)
    return sentences


def get_index(metadata, last_item, start_trim):
    """
    try:
        index = metadata.items.index(last_item) if last_item else 0
        refItem = metadata.items[index]
    except ValueError:
        print("Last item not found")
    """
    index = 0
    for item in metadata.items:
        if (
                (item.character == last_item[0]) and
                (item.start_time > (last_item[1] - start_trim))
        ):
            return index + 1  # take the next one
        else:
            index += 1
    return 0


def saveVTT(video, webvtt):
    msg = "\nSAVE TRANSCRIPT WEBVTT : %s" % time.ctime()
    lang = video.main_lang
    temp_vtt_file = NamedTemporaryFile(suffix='.vtt')
    webvtt.save(temp_vtt_file.name)
    if webvtt.captions:
        msg += "\nstore vtt file in bdd with CustomFileModel model file field"
        if FILEPICKER:
            videodir, created = UserFolder.objects.get_or_create(
                name='%s' % video.slug,
                owner=video.owner)
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
                created_by=video.owner)
            if subtitleFile.file and os.path.isfile(subtitleFile.file.path):
                os.remove(subtitleFile.file.path)
        else:
            subtitleFile, created = CustomFileModel.objects.get_or_create()

        subtitleFile.file.save("subtitle_%s_%s.vtt" % (
            lang, time.strftime("%Y%m%d-%H%M%S")), File(temp_vtt_file))
        msg += "\nstore vtt file in bdd with Track model src field"

        subtitleVtt, created = Track.objects.get_or_create(
            video=video, lang=lang)
        subtitleVtt.src = subtitleFile
        subtitleVtt.lang = lang
        subtitleVtt.save()
    else:
        msg += "\nERROR SUBTITLES Output size is 0"
    return msg
