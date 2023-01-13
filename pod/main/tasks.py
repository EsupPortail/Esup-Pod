from celery import shared_task
tasks_list = {}


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
    tasks_list[slug] = self.request.id
    #transcribe(url, slug)


@shared_task(bind=True)
def task_end_live_transcription(self, slug):
    print("CELERY END LIVE TRANSCRIPTION %s" % slug)
    tasks_id = tasks_list.pop(slug, None)
    if tasks_id:
        self.app.control.revoke(tasks_id, terminate=True, signal="SIGKILL")
