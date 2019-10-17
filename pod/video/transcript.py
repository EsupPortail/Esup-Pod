#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings

from deepspeech import Model
import numpy as np
import shlex
import subprocess

try:
    from shhlex import quote
except ImportError:
    from pipes import quote

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

    #print(mp3file)

    # print(convert_samplerate(mp3file.path, desired_sample_rate))

    audio = convert_samplerate(mp3file.path, desired_sample_rate)[1]

    return "Main Transcript"

    # ffmpeg -i audio_192k_6761.mp3 -acodec pcm_s16le -ac 1 -ar 16000 6761.wav

    # video 6734
    """
    ds_model = None
    if all([cond in DS_PARAM[lang]
            for cond in ['model', 'alphabet', 'beam_width']]):
        ds_model = deepspeech.Model(
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
    """

    """
    output_dir = os.path.join(
        os.path.dirname(video.video.path),
        "%04d" % video.id)
    msg, ds_wav_path = av2wav16b16k(video, output_dir)
    msg += deepspeech_run(video, ds_wav_path)
    msg += "\nDELETE TEMP WAV 16BIT 16KHZ"
    os.remove(ds_wav_path)
    return msg
    """
