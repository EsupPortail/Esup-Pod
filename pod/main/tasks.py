"""Esup-Pod main tasks."""

from pod.main.celery import app
from pod.live.models import LiveTranscriptRunningTask, Broadcaster


@app.task(bind=True)
def task_start_encode(self, video_id: int) -> None:
    """Start video encoding with Celery."""
    print("CELERY START ENCODE VIDEO ID %s" % video_id)
    from pod.video_encode_transcript.encode import encode_video

    encode_video(video_id)


@app.task(bind=True)
def task_start_transcript(self, video_id: int) -> None:
    """Start video transcripting with Celery."""
    print("CELERY START TRANSCRIPT VIDEO ID %s" % video_id)
    from pod.video_encode_transcript.transcript import main_threaded_transcript

    main_threaded_transcript(video_id)


@app.task(bind=True)
def task_start_encode_studio(
    self, recording_id: int, video_output, videos, subtime, presenter
) -> None:
    """Start studio record encoding with Celery."""
    print("CELERY START ENCODE VIDEOS FROM STUDIO RECORDING ID %s" % recording_id)
    from pod.video_encode_transcript.encode import encode_video_studio

    encode_video_studio(recording_id, video_output, videos, subtime, presenter)


@app.task(bind=True)
def task_start_live_transcription(self, url, slug, model, filepath) -> None:
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
def task_end_live_transcription(self, slug) -> None:
    """End live transcription with Celery."""
    print("CELERY END LIVE TRANSCRIPTION %s" % slug)
    broadcaster = Broadcaster.objects.get(slug=slug)
    running_task = LiveTranscriptRunningTask.objects.get(broadcaster=broadcaster)
    if running_task:
        self.app.control.revoke(running_task.task_id, terminate=True)
        running_task.delete()


@app.task(bind=True)
def task_start_bbb_presentation_encode_and_upload_to_pod(
    self, record_id: int, url: str, extension: str
) -> None:
    """Start BBB presentation encoding with Celery, then upload to Pod."""
    print("CELERY START BBB ENCODE PRESENTATION/UPLOAD RECORD ID %s" % record_id)
    from pod.import_video.views import bbb_encode_presentation_and_upload_to_pod

    bbb_encode_presentation_and_upload_to_pod(record_id, url, extension)


@app.task(bind=True)
def task_start_bbb_presentation_encode_and_move_to_destination(
    self, filename: str, url: str, dest_file: str
) -> None:
    """Start BBB presentation encoding with Celery, then move the video file."""
    print("CELERY START BBB ENCODE PRESENTATION/MOVE %s" % filename)
    from pod.import_video.views import bbb_encode_presentation_and_move_to_destination

    bbb_encode_presentation_and_move_to_destination(filename, url, dest_file)
