"""Esup-Pod live transcription."""

from django.conf import settings
from vosk import Model, KaldiRecognizer, SetLogLevel
from webvtt import WebVTT, Caption
from pod.main.tasks import task_end_live_transcription, task_start_live_transcription
import threading
import time
import json
import subprocess

LIVE_CELERY_TRANSCRIPTION = getattr(settings, "LIVE_CELERY_TRANSCRIPTION ", False)
LIVE_VOSK_MODEL = getattr(settings, "LIVE_VOSK_MODEL", None)
__SAMPLE_RATE__ = 16000
threads = {}
threads_to_stop = []
SetLogLevel(-1)


def timestring(seconds: int) -> str:
    """Convert a number of seconds to a timestring."""
    minutes = seconds / 60
    seconds = seconds % 60
    hours = int(minutes / 60)
    minutes = int(minutes % 60)
    return "%i:%02i:%06.3f" % (hours, minutes, seconds)


def transcribe(url, slug, model, filepath) -> None:
    """Transcribe a live video."""
    # if url.endswith(".m3u8"):
    #    url = url.split(".m3u8")[0] + "_mid/index.m3u8"
    trans_model = Model(model)
    rec = KaldiRecognizer(trans_model, __SAMPLE_RATE__)
    rec.SetWords(True)
    last_caption = None
    thread_id = threading.get_ident()
    while LIVE_CELERY_TRANSCRIPTION or thread_id not in threads_to_stop:
        start = time.time()
        command = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "quiet",
            "-i",
            url,
            "-ss",
            "00:00:00.005",
            "-t",
            "00:00:05",
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            str(__SAMPLE_RATE__),
            "-f",
            "s16le",
            "-",
        ]
        with subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as process:
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

            caption_text = handle_last_caption(last_caption, caption_text)

            current_start = timestring(0)
            current_end = timestring(86400)
            if caption_text != "":
                caption = Caption(current_start, current_end, caption_text)
                last_caption = caption
                # print(caption_text)
                vtt.captions.append(caption)
                # save or return webvtt
                vtt.save(filepath)

        now = time.time() - start
        if now < 5:
            time.sleep(5 - now)
    # print("stopped transcription")
    threads_to_stop.remove(thread_id)
    vtt = WebVTT()
    vtt.save(filepath)


def handle_last_caption(last_caption, caption_text) -> None:
    """Handle the last caption."""

    if last_caption:
        last_caption_text, current_caption_text = (
            last_caption.text.strip(),
            caption_text.strip(),
        )
        last_caption_words, current_caption_words = last_caption_text.split(
            " "
        ), current_caption_text.split(" ")
        current_caption_words1 = current_caption_words[1 : len(current_caption_words)]

        for i in range(len(last_caption_words) - 1, 0, -1):
            if (
                last_caption_words[-i:] == current_caption_words[:i]
                or last_caption_words[-i:] == current_caption_words1[:i]
            ):
                caption_text = " ".join(current_caption_words[i:])
                break
        if last_caption_text in caption_text:
            caption_text = caption_text.replace(last_caption_text, "").strip()
        if caption_text in last_caption_text:
            caption_text = caption_text.replace(caption_text, "").strip()
    return caption_text


def transcribe_live(url, slug, status, lang, filepath) -> None:
    if LIVE_VOSK_MODEL and LIVE_VOSK_MODEL.get(lang):
        model = LIVE_VOSK_MODEL.get(lang).get("model")
        if LIVE_CELERY_TRANSCRIPTION:
            if status:
                task_start_live_transcription.delay(url, slug, model, filepath)
            else:
                vtt = WebVTT()
                vtt.save(filepath)
                task_end_live_transcription.delay(slug)
        else:
            if status:
                # print("main process")
                t = threading.Thread(target=transcribe, args=(url, slug, model, filepath))
                t.daemon = True
                t.start()
                # get id of the thread
                threads[slug] = t.ident

            else:
                vtt = WebVTT()
                vtt.save(filepath)
                stop_thread = threads.get(slug, None)
                if stop_thread:
                    threads_to_stop.append(stop_thread)
                    # print("stopping thread")
