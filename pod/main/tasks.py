"""Esup-Pod main tasks."""

from pod.main.celery import app
from pod.live.models import LiveTranscriptRunningTask, Broadcaster


@app.task(bind=True)
def task_start_encode(self, video_id):
    """Start video encoding with Celery."""
    print("CELERY START ENCODE VIDEO ID %s" % video_id)
    from pod.video_encode_transcript.encode import encode_video

    encode_video(video_id)


@app.task(bind=True)
def task_start_transcript(self, video_id):
    """Start video transcripting with Celery."""
    print("CELERY START TRANSCRIPT VIDEO ID %s" % video_id)
    from pod.video_encode_transcript.transcript import main_threaded_transcript

    main_threaded_transcript(video_id)


@app.task(bind=True)
def task_start_bbb_encode(self, meeting_id):
    """Start BBB meeting encoding with Celery."""
    print("CELERY START BBB ENCODE MEETING ID %s" % meeting_id)
    from pod.bbb.bbb import bbb_encode_meeting

    bbb_encode_meeting(meeting_id)


@app.task(bind=True)
def task_start_encode_studio(
    self, recording_id, video_output, videos, subtime, presenter
):
    """Start studio record encoding with Celery."""
    print("CELERY START ENCODE VIDEOS FROM STUDIO RECORDING ID %s" % recording_id)
    from pod.video_encode_transcript.encode import encode_video_studio

    encode_video_studio(recording_id, video_output, videos, subtime, presenter)


@app.task(bind=True)
def task_start_live_transcription(self, url, slug, model, filepath):
    """Start live transcription with Celery."""
    print("CELERY START LIVE TRANSCRIPTION %s" % slug)
    from pod.live.live_transcript import transcribe

    broadcaster = Broadcaster.objects.get(slug=slug)
    running_task = LiveTranscriptRunningTask.objects.create(
        broadcaster=broadcaster, task_id=self.request.id
    )
    running_task.save()
    transcribe(url, slug, model, filepath)


@app.task(bind=True)
def task_end_live_transcription(self, slug):
    """End live transcription with Celery."""
    print("CELERY END LIVE TRANSCRIPTION %s" % slug)
    broadcaster = Broadcaster.objects.get(slug=slug)
    running_task = LiveTranscriptRunningTask.objects.get(broadcaster=broadcaster)
    if running_task:
        self.app.control.revoke(running_task.task_id, terminate=True)
        running_task.delete()
