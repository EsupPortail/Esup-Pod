#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings

from deepspeech import Model
import numpy as np
import shlex
import subprocess
import sys
from timeit import default_timer as timer
from datetime import timedelta

from webvtt import WebVTT, Caption

try:
    from shhlex import quote
except ImportError:
    from pipes import quote

DS_PARAM = getattr(settings, 'DS_PARAM', dict())

if getattr(settings, 'USE_PODFILE', False):
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder
    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel


def convert_samplerate(audio_path, desired_sample_rate):
    sox_cmd = 'sox {} --type raw --bits 16 --channels 1 --rate {} --encoding signed-integer --endian little --compression 0.0 --no-dither - '.format(
        quote(audio_path), desired_sample_rate)
    try:
        output = subprocess.check_output(
            shlex.split(sox_cmd), stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('SoX returned non-zero status: {}'.format(e.stderr))
    except OSError as e:
        raise OSError(e.errno, 'SoX not found, use {}hz files or install it: {}'.format(
            desired_sample_rate, e.strerror))

    return desired_sample_rate, np.frombuffer(output, np.int16)


# #################################
# TRANSCRIPT VIDEO : MAIN FUNCTION
# #################################
def main_transcript(video_to_encode):

    desired_sample_rate = 16000

    mp3file = video_to_encode.get_video_mp3(
    ).source_file if video_to_encode.get_video_mp3() else None

    lang = video_to_encode.main_lang

    ds_model = Model(
        DS_PARAM[lang]['model'], DS_PARAM[lang]['alphabet'],
        DS_PARAM[lang]['beam_width']
    )

    if all([cond in DS_PARAM[lang]
            for cond in ['alphabet', 'lm', 'trie',
                         'lm_alpha', 'lm_beta']]):
        ds_model.enableDecoderWithLM(
            DS_PARAM[lang]['lm'], DS_PARAM[lang]['trie'],
            DS_PARAM[lang]['lm_alpha'], DS_PARAM[lang]['lm_beta']
        )

    fn, audio = convert_samplerate(mp3file.path, desired_sample_rate)

    print('Running inference.', file=sys.stderr)
    inference_start = timer()
    metadata = ds_model.sttWithMetadata(audio)
    print('Confidence : %s' % metadata.confidence)

    sentences = []
    sentence = []
    refItem = metadata.items[0]
    sentencemaxlength = 3  # time in sec for phrase length
    for item in metadata.items:
        if((item.start_time - refItem.start_time) < sentencemaxlength):
            sentence.append(item)
        else:
            if item.character == ' ':
                sentences.append(sentence)
                sentence = []
                refItem = item
            else:
                sentence.append(item)

    vtt = WebVTT()

    str_sentence = ''
    for sentence in sentences:
        # print(sentence[0].start_time,sentence[len(sentence)-1].start_time)
        for item in sentence:
            str_sentence = str_sentence + item.character

        caption = Caption(
            '%s.%s' % (timedelta(seconds=int(str(sentence[0].start_time).split('.')[0])), str(
                '%.3f' % sentence[0].start_time).split('.')[1]),
            '%s.%s' % (timedelta(seconds=int(str(sentence[-1].start_time).split('.')[0])), str(
                '%.3f' % sentence[-1].start_time).split('.')[1]),
            ['%s' % str_sentence]
        )

        vtt.captions.append(caption)
        str_sentence = ''

    print(vtt) # TOD SAVE VTT FILE

    inference_end = timer() - inference_start
    print('Inference took %0.3fs.' %
          (inference_end), file=sys.stderr)

    return "Main Transcript"
