from django.conf import settings
from django.core.files import File
from pod.completion.models import Track

from deepspeech import Model
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

log = logging.getLogger(__name__)


def start_transcript(video):
    log.info("START TRANSCRIPT VIDEO %s" % video)
    t = threading.Thread(target=main_threaded_transcript,
                         args=[video])
    t.setDaemon(True)
    t.start()


def main_threaded_transcript(video_to_encode):
    remove_encoding_in_progress = False
    if not video_to_encode.encoding_in_progress:
        remove_encoding_in_progress = True
        video_to_encode.encoding_in_progress = True
        video_to_encode.save()

    msg = main_transcript(video_to_encode)

    if DEBUG:
        print(msg)

    if remove_encoding_in_progress:
        video_to_encode.encoding_in_progress = False
        video_to_encode.save()


def convert_samplerate(audio_path, desired_sample_rate, trim_start, duration):
    # trim 0 1800
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


# #################################
# TRANSCRIPT VIDEO : MAIN FUNCTION
# #################################
def main_transcript(video_to_encode):
    msg = ""

    mp3file = video_to_encode.get_video_mp3(
    ).source_file if video_to_encode.get_video_mp3() else None

    lang = video_to_encode.main_lang

    # check if DS_PARAM [lang] exist
    if not DS_PARAM.get(lang):
        msg += "\n no deepspeech model found for lang:%s." % lang
        msg += "Please add it in DS_PARAM."
        return msg

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

    desired_sample_rate = ds_model.sampleRate()

    webvtt = WebVTT()
    inference_start = timer()
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
            mp3file.path, desired_sample_rate, start_trim, duration)
        msg += '\nRunning inference.'

        metadata = ds_model.sttWithMetadata(audio)

        msg += '\nConfidence : %s' % metadata.confidence

        sentences[:] = []  # empty list
        sentence[:] = []  # empty list

        refItem = metadata.items[0]

        index = get_index(metadata, last_item, start_trim) if last_item else 0

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
