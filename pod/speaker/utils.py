"""Esup-Pod speaker utilities."""

from typing import Optional, Dict, List
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


def get_video_speakers_grouped(video) -> Dict[Speaker, List[str]]:
    """
    Group the jobs by speaker for a given video.

    Args:
        video (Video): The video for which to group the speakers.

     Returns:
        Dict[Speaker, List[str]]: A dictionary where the keys are the speakers (Speaker)
        and the values are lists of job titles (str) associated with each speaker.
    """
    speakers = video.jobvideo_set.select_related("job__speaker").all()
    grouped_speakers = {}
    for jobvideo in speakers:
        speaker = jobvideo.job.speaker
        if speaker not in grouped_speakers:
            grouped_speakers[speaker] = []
        grouped_speakers[speaker].append(jobvideo.job.title)
    return grouped_speakers
