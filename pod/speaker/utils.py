"""Esup-Pod speaker utilities."""

from typing import Optional
from pod.speaker.models import Speaker


def get_all_speakers() -> Optional[Speaker]:
    """
    Retrieve the speakers list.

    Returns:
        Optional[Speakers]: The speakers list, or None if no speaker is found.
    """
    return Speaker.objects.prefetch_related('job_set').all()
