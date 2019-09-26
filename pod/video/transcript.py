from django.conf import settings

from django.core.files import File
from pod.completion.models import Track

from webvtt import WebVTT, Caption
from tempfile import NamedTemporaryFile

import os
import subprocess
import deepspeech
import numpy
import time
import billiard

from timeit import default_timer as timer
from pod.video.voiceActivityDetector import VoiceActivityDetector

if getattr(settings, 'USE_PODFILE', False):
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder
    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel

FFMPEG = getattr(settings, 'FFMPEG', 'ffmpeg')
FFMPEG_NB_THREADS = getattr(settings, 'FFMPEG_NB_THREADS', 0)

DS_PARAM = getattr(settings, 'DS_PARAM', dict())

NB_WORKERS_POOL = max(
    getattr(settings, 'NB_WORKERS_POOL', 4), 1)

DEBUG = getattr(settings, 'DEBUG', False)


# ######################################
# TRANSCRIPT VIDEO : DEEPSPEECH PROCESS
# ######################################
def initfunc(lang):
    global ds_model
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


def deepspeech_run(video, ds_wav_path):
    msg = msg = "\nTRANSCRIPTING FILE : %s" % time.ctime()
    if DEBUG:
        start_timer = timer()
    lang = video.main_lang
    vad = VoiceActivityDetector(ds_wav_path)
    seg_list, sample_rate = vad.vad_segment_generator()
    if seg_list:
        msg += "\n- Start Transcript Process : %s" % time.ctime()
        p = billiard.Pool(processes=NB_WORKERS_POOL,
                          initializer=initfunc,
                          initargs=(lang,),
                          threads=True)
        res = p.map_async(deepspeech_aux, seg_list).get()
        p.close()
        p.join()
        msg += "\n- End Transcript Process : %s" % time.ctime()
    if DEBUG:
        end_timer = timer()
        print('Transcription duration : %f s' %
              (end_timer - start_timer))
    msg2, webvtt = createVTT(res, vad.sample_rate)
    msg += msg2
    msg += saveVTT(video, webvtt)
    return msg


def deepspeech_aux(arg):
    if ds_model:
        start, end, data, rate = arg
        data_window = numpy.frombuffer(data, dtype=numpy.int16)
        res = ds_model.stt(data_window, rate)
        return (start, end, res)


# ###############################################
# TRANSCRIPT VIDEO : FILE CONVERSION 16KHZ 16BIT
# ###############################################
def av2wav16b16k(video, output_dir):
    """
    Convert video or audio file into Wave format 16bit 16kHz mono
    """
    path_in = video.video.path
    name = os.path.splitext(os.path.basename(path_in))[0]
    path_out = os.path.join(output_dir, name + "_ds.wav")
    options = "-format wav -acodec pcm_s16le -ar 16000 \
               -threads %(nb_threads)s" % {
                   'nb_threads': FFMPEG_NB_THREADS
                }
    cmd = "%(ffmpeg)s -i %(input)s %(options)s %(output)s" % {
        'ffmpeg': FFMPEG,
        'input': path_in,
        'options': options,
        'output': path_out
    }
    msg = "\nffmpegWav16bit16kHzCommand :\n%s" % cmd
    msg += "\n- Encoding Wav 16bit 16kHz : %s" % time.ctime()
    ffmpeg = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    msg += "\n- End Encoding Wav 16bit 16kHz : %s" % time.ctime()

    with open(output_dir + "/encoding.log", "ab") as f:
        f.write(b'\n\nffmpegwav16bit16kHz:\n\n')
        f.write(ffmpeg.stdout)

    return msg, path_out


# ###########################################
# TRANSCRIPT VIDEO : WEBVTT FILES MANAGEMENT
# ###########################################
def createCaption(arg, rate):
    start, end, text = arg
    start = format(start/rate, '.3f')
    end = format(end/rate, '.3f')
    start_time = time.strftime(
        '%H:%M:%S',
        time.gmtime(int(str(start).split('.')[0]))
    )
    start_time += ".%s" % (str(start).split('.')[1])
    end_time = time.strftime(
        '%H:%M:%S',
        time.gmtime(int(str(end).split('.')[0])))
    end_time += ".%s" % (str(end).split('.')[1])
    caption = Caption(
        '%s' % start_time,
        '%s' % end_time,
        '%s' % text
    )
    return caption


def createVTT(content_l, rate):
    msg = "\nCREATE TRANSCRIPT WEBVTT : %s" % time.ctime()
    webvtt = WebVTT()
    webvtt.captions.extend([createCaption(e, rate) for e in content_l if e[2]])
    return msg, webvtt


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
            previousSubtitleFile = CustomFileModel.objects.filter(
                name__startswith="subtitle_%s" % lang,
                folder=videodir,
                created_by=video.owner
            )
            for subt in previousSubtitleFile:
                subt.delete()
            subtitleFile, created = CustomFileModel.objects.get_or_create(
                name="subtitle_%s" % lang,
                folder=videodir,
                created_by=video.owner)
            if subtitleFile.file and os.path.isfile(subtitleFile.file.path):
                os.remove(subtitleFile.file.path)
        else:
            subtitleFile, created = CustomFileModel.objects.get_or_create()
        subtitleFile.file.save("subtitle_%s.vtt" % lang, File(temp_vtt_file))
        msg += "\nstore vtt file in bdd with Track model src field"
        subtitleVtt, created = Track.objects.get_or_create(video=video)
        subtitleVtt.src = subtitleFile
        subtitleVtt.lang = lang
        subtitleVtt.save()
    else:
        msg += "\nERROR SUBTITLES Output size is 0"
    return msg


# #################################
# TRANSCRIPT VIDEO : MAIN FUNCTION
# #################################
def main_transcript(video):
    output_dir = os.path.join(
        os.path.dirname(video.video.path),
        "%04d" % video.id)
    msg, ds_wav_path = av2wav16b16k(video, output_dir)
    msg += deepspeech_run(video, ds_wav_path)
    msg += "\nDELETE TEMP WAV 16BIT 16KHZ"
    os.remove(ds_wav_path)
    return msg
