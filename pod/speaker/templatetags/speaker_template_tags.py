"""Template tags for the speaker app."""

from django import template


from pod.speaker.utils import get_video_speakers, get_video_speakers_grouped
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


@register.simple_tag(name="get_video_speaker_grouped")
def get_video_speaker_grouped(video: Video) -> dict:
    """
    Group the jobs by speaker for a given video.

    Args:
        video (Video): The video for which to group the speakers.

    Returns:
        List[VideoJob]: A list of VideoJob objects representing the speakers associated with the video.
    """

    return get_video_speakers_grouped(video)
