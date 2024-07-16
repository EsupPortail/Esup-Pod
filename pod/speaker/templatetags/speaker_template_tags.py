"""Template tags for the speaker app."""

from django import template


from pod.speaker.utils import get_video_speakers
from pod.video.models import Video


register = template.Library()


@register.simple_tag(name="get_video_speaker")
def get_video_speaker(video: Video) -> list:
    """
    Get all speaker for a video.

    Args:
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        list (:class:`list(pod.speaker.models.VideoJob)`): The list of speakers job.
    """
    return get_video_speakers(video)
