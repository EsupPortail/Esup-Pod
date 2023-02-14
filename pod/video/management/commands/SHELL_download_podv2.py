"""Download contents from Pod v1."""

from django.core.management import call_command
from pod.video.models import Video

Video.objects.all().count()

# Download videos id 1:3000
list_videos = Video.objects.all().order_by("id")
for vid in list_videos[1:3000]:
    call_command("download_video_source_file", vid.id)

# Download one video
call_command("download_video_source_file", 2184)

list_user = [37]

# Download all videos in filter
list_videos = Video.objects.filter(owner_id__in=list_user).order_by("id")
for vid in list_videos[11:20]:
    call_command("download_video_source_file", vid.id)


video_id = [5131, 2091]

# Download all videos in filter
list_videos = Video.objects.filter(id__in=video_id).order_by("id")
for vid in list_videos:
    call_command("download_video_source_file", vid.id)
