"""Esup-Pod speaker utilities."""

from typing import Optional
from pod.speaker.models import Speaker, JobVideo
from pod.video.models import Video


def get_all_speakers() -> Optional[Speaker]:
    """
    Retrieve the speakers list.

    Returns:
        Optional[Speakers]: The speakers list, or None if no speaker is found.
    """
    return Speaker.objects.prefetch_related("job_set").all()


def get_video_speakers(video: Video) -> Optional[JobVideo]:
    """
    Retrieve the speakers associated with a given video.

    Args:
        video (Video): The video for which to retrieve the speakers.

    Returns:
        Optional[JobVideo]: The jobs associated with the video, or None if no job is found.
    """
    return JobVideo.objects.filter(video=video)
