from celery import shared_task


@shared_task(bind=True)
def task_start_encode(self, video_id):
    print("CELERY START ENCODE VIDEO ID %s" % video_id)
    # from pod.video.encode import encode_video
    # encode_video(video_id)
