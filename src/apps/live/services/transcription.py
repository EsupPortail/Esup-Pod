"""
Esup-Pod - Live transcription service.

Provides real-time transcription using Vosk and FFmpeg.
Ported from V4 pod/live/live_transcript.py
"""

import json
import logging
import subprocess
import threading
import time

from django.conf import settings
from vosk import KaldiRecognizer, Model, SetLogLevel
from webvtt import Caption, WebVTT

from src.apps.live.conf import live_settings

logger = logging.getLogger(__name__)

__SAMPLE_RATE__ = 16000
threads = {}
threads_to_stop = []
SetLogLevel(-1)


def timestring(seconds: float) -> str:
    """Convert a number of seconds to a WebVTT timestring."""
    minutes = seconds / 60
    seconds = seconds % 60
    hours = int(minutes / 60)
    minutes = int(minutes % 60)
    return "%02i:%02i:%06.3f" % (hours, minutes, seconds)


def handle_last_caption(last_caption: Caption, caption_text: str) -> str:
    """Deduplicate overlapping phrases between the last caption and the new one."""
    if last_caption:
        last_caption_text = last_caption.text.strip()
        current_caption_text = caption_text.strip()
        last_caption_words = last_caption_text.split(" ")
        current_caption_words = current_caption_text.split(" ")
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


def transcribe(url: str, slug: str, model_path: str, filepath: str) -> None:  # noqa: C901
    """
    Transcribe a live video stream.

    Connects to the stream using ffmpeg, decodes audio, and passes
    it to Vosk for speech-to-text generation.
    """
    logger.info("Starting transcription for %s using model %s", slug, model_path)
    try:
        trans_model = Model(model_path)
    except Exception as exc:
        logger.error("Failed to load Vosk model from %s: %s", model_path, exc)
        return

    rec = KaldiRecognizer(trans_model, __SAMPLE_RATE__)
    rec.SetWords(True)
    last_caption = None
    thread_id = threading.get_ident()

    while live_settings.use_live_transcription or thread_id not in threads_to_stop:
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
        try:
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
                for res in results:
                    words = json.loads(res).get("result")
                    if not words:
                        continue
                    content = " ".join([w["word"] for w in words])
                    caption_text += content + " "

                caption_text = handle_last_caption(last_caption, caption_text)

                current_start = timestring(0)
                current_end = timestring(86400)
                if caption_text != "":
                    caption = Caption(current_start, current_end, caption_text)
                    last_caption = caption
                    vtt.captions.append(caption)
                    vtt.save(filepath)

        except Exception as exc:
            logger.error("Transcription error for %s: %s", slug, exc)

        now = time.time() - start
        if now < 5:
            time.sleep(5 - now)

    logger.info("Stopped transcription for %s", slug)
    if thread_id in threads_to_stop:
        threads_to_stop.remove(thread_id)
    vtt = WebVTT()
    vtt.save(filepath)


def transcribe_live(url: str, slug: str, status: bool, lang: str, filepath: str) -> None:
    """
    Helper to dispatch the transcription process either via Celery
    or a local Daemon Thread.
    """
    vosk_models = getattr(settings, "LIVE_VOSK_MODEL", None)
    if not vosk_models or not vosk_models.get(lang):
        logger.warning("No Vosk model configured for language '%s'", lang)
        return

    model_path = vosk_models.get(lang).get("model")

    if live_settings.use_live_transcription:
        from src.apps.live.tasks import (
            start_live_transcription_task,
            end_live_transcription_task,
        )

        if status:
            start_live_transcription_task.delay(url, slug, model_path, filepath)
        else:
            vtt = WebVTT()
            vtt.save(filepath)
            end_live_transcription_task.delay(slug)
    else:
        # Fallback to threading if Celery isn't specifically enforcing
        if status:
            t = threading.Thread(
                target=transcribe, args=(url, slug, model_path, filepath)
            )
            t.daemon = True
            t.start()
            threads[slug] = t.ident
        else:
            vtt = WebVTT()
            vtt.save(filepath)
            stop_thread = threads.get(slug, None)
            if stop_thread:
                threads_to_stop.append(stop_thread)
