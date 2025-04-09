from celery import shared_task
from django.utils.timezone import now
from .models import Video

@shared_task
def publish_scheduled_videos():
    videos_to_publish = Video.objects.filter(
        scheduled_publish_date__lte=now(), 
        is_published=False
    )
    for video in videos_to_publish:
        video.is_published = True
        video.save()