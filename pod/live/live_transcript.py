import os
from django.conf import settings
from vosk import Model, KaldiRecognizer, SetLogLevel
from webvtt import WebVTT, Caption
from pod.main.tasks import task_end_live_transcription, task_start_live_transcription
import threading
import time
import json
import subprocess

CELERY_TO_TRANSCRIBE_LIVE = getattr(settings, "CELERY_TO_TRANSCRIBE_LIVE", False)
VOSK_MODEL = getattr(settings, "LIVE_TRANSCRIPTION_MODEL", None)

TRANSCRIPTIONS_FOLDER = getattr(settings, "TRANSCRIPTIONS_FOLDER", None)
threads = {}
threads_to_stop = []


def timestring(seconds):
    minutes = seconds / 60
    seconds = seconds % 60
    hours = int(minutes / 60)
    minutes = int(minutes % 60)
    return "%i:%02i:%06.3f" % (hours, minutes, seconds)


def transcribe(url, slug, model):
    filename = slug + ".vtt"
    save_path = os.path.join(TRANSCRIPTIONS_FOLDER, filename)
    url = url.split('.m3u8')[0] + "_low/index.m3u8"
    SAMPLE_RATE = 16000
    SetLogLevel(-1)
    print(model)
    trans_model = Model(model)
    rec = KaldiRecognizer(trans_model, SAMPLE_RATE)
    rec.SetWords(True)
    last_caption = None
    thread_id = threading.get_ident()
    while CELERY_TO_TRANSCRIBE_LIVE or thread_id not in threads_to_stop:
        start = time.time()
        command = ["ffmpeg", "-y", "-loglevel", "quiet", "-i", url, "-ss", "00:00:00.005", "-t",
                   "00:00:05", "-acodec", "pcm_s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "s16le", "-"]

        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            results = []
            data = process.stdout.read(4000)
            while True:
                if len(data) == 0:
                    break
                else:
                    data = process.stdout.read(4000)
                if rec.AcceptWaveform(data):
                    results.append(rec.Result())

            results.append(rec.FinalResult())

            vtt = WebVTT()
            caption_text = ""
            for _, res in enumerate(results):
                words = json.loads(res).get("result")
                if not words:
                    continue

                # start = timestring(words[0]["start"])

                # end = timestring(words[-1]["end"])
                content = " ".join([w["word"] for w in words])
                caption_text += content + " "
            if last_caption:
                last_caption_text, current_caption_text = last_caption.text.strip(), caption_text.strip()
                last_caption_words, current_caption_words = last_caption_text.split(
                    " "), current_caption_text.split(" ")
                current_caption_words1 = current_caption_words[1:len(
                    current_caption_words)]

                for i in range(len(last_caption_words) - 1, 0, -1):
                    if last_caption_words[-i:] == current_caption_words[:i] or last_caption_words[-i:] == current_caption_words1[:i]:
                        # print(" ".join(last_caption_words[-i:]) + " ----------- " +
                        #      " ".join(current_caption_words[:i]))
                        caption_text = " ".join(current_caption_words[i:])
                        break
                if last_caption_text in caption_text:
                    caption_text = caption_text.replace(
                        last_caption_text, "").strip()
                if caption_text in last_caption_text:
                    caption_text = caption_text.replace(
                        caption_text, "").strip()

            current_start = timestring(0)
            current_end = timestring(86400)
            if caption_text != "":
                caption = Caption(current_start, current_end,
                                  caption_text)
                last_caption = caption
                print(caption_text)
                vtt.captions.append(caption)
                # save or return webvtt
                vtt.save(save_path)

        now = time.time() - start
        if now < 5:
            time.sleep(5 - now)
    print("stopped transcription")
    threads_to_stop.remove(thread_id)


def transcribe_live(url, slug, status, lang):
    print(lang)
    if VOSK_MODEL and VOSK_MODEL.get(lang):
        model = VOSK_MODEL.get(lang).get("model")
        if CELERY_TO_TRANSCRIBE_LIVE:
            if status:
                task_start_live_transcription.delay(url, slug, model)
            else:
                task_end_live_transcription.delay(slug)
        else:
            if status:
                print("main process")
                t = threading.Thread(target=transcribe, args=(
                    url, slug, model))
                t.setDaemon(True)
                t.start()
                # get id of the thread
                threads[slug] = t.ident

            else:
                stop_thread = threads.get(slug, None)
                if stop_thread:
                    threads_to_stop.append(stop_thread)
                    print("stopping thread")
