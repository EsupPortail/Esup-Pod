from django.conf import settings
from vosk import Model, KaldiRecognizer, SetLogLevel
from webvtt import WebVTT, Caption
import threading
import time
import json
import subprocess
from pod.main.tasks import task_end_live_transcription, task_start_live_transcription

CELERY_TO_TRANSCRIBE_LIVE = getattr(settings, "CELERY_TO_TRANSCRIBE_LIVE", False)
path_to_media_folder = r"C:\Users\mateo\Desktop\django_projects\podv3\pod\media\transcripts"


def timestring(seconds):
    minutes = seconds / 60
    seconds = seconds % 60
    hours = int(minutes / 60)
    minutes = int(minutes % 60)
    return "%i:%02i:%06.3f" % (hours, minutes, seconds)


def transcribe(url, slug):
    save_path = path_to_media_folder + "\\" + slug + ".vtt"
    url = url.split('.m3u8')[0] + "_low/index.m3u8"
    SAMPLE_RATE = 16000
    SetLogLevel(-1)
    small_model = r"C:\Users\mateo\Desktop\transcription\vosk-model-small-fr-0.22"

    model = Model(small_model)
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(True)
    last_caption = None
    while True:
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


def transcribe_live(url, slug, status):
    if CELERY_TO_TRANSCRIBE_LIVE:
        if status:
            task_start_live_transcription.delay(url, slug)
        else:
            task_end_live_transcription.delay(slug)
    else:
        if status:
            print("main process")
            t = threading.Thread(target=transcribe, args=(
                url, slug))
            t.setDaemon(True)
            t.start()
        else:
            print("end process")


def end_live_transcription():
    print("end live transcription")
