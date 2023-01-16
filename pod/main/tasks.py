from celery import shared_task
from pod.live.models import RunningTask, Broadcaster


@shared_task(bind=True)
def task_start_encode(self, video_id):
    print("CELERY START ENCODE VIDEO ID %s" % video_id)
    from pod.video.encode import encode_video

    encode_video(video_id)


@shared_task(bind=True)
def task_start_transcript(self, video_id):
    print("CELERY START TRANSCRIPT VIDEO ID %s" % video_id)
    from pod.video.transcript import main_threaded_transcript

    main_threaded_transcript(video_id)


@shared_task(bind=True)
def task_start_bbb_encode(self, meeting_id):
    print("CELERY START BBB ENCODE MEETING ID %s" % meeting_id)
    from pod.video.bbb import bbb_encode_meeting

    bbb_encode_meeting(meeting_id)


@shared_task(bind=True)
def task_start_encode_studio(
    self, recording_id, video_output, videos, subtime, presenter
):
    print("CELERY START ENCODE VIDEOS FROM STUDIO RECORDING ID %s" % recording_id)
    from pod.video.encode import encode_video_studio

    encode_video_studio(recording_id, video_output, videos, subtime, presenter)


@shared_task(bind=True)
def task_start_live_transcription(self, url, slug):
    print("CELERY START LIVE TRANSCRIPTION %s" % slug)
    from pod.live.live_transcript import transcribe
    #transcribe(url, slug)
    broadcaster = Broadcaster.objects.get(slug=slug)
    running_task = RunningTask.objects.create(
        broadcaster=broadcaster, task_id=self.request.id
    )
    running_task.save()
    # transcribe(url, slug)


@shared_task(bind=True)
def task_end_live_transcription(self, slug):
    print("CELERY END LIVE TRANSCRIPTION %s" % slug)
    broadcaster = Broadcaster.objects.get(slug=slug)
    running_task = RunningTask.objects.get(broadcaster=broadcaster)
    if running_task:
        self.app.control.revoke(running_task.task_id, terminate=True)
        running_task.delete()
