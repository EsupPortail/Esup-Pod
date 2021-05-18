from celery import shared_task


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
