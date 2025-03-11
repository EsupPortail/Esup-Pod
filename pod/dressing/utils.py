"""Esup-Pod dressing utilities."""

import os
from .models import Dressing
from django.conf import settings
from django.db.models import Q


def get_dressing_input(dressing: Dressing, ffmpeg_dressing_input: str) -> str:
    """
    Obtain the files necessary for encoding a dressed video.

    Args:
        dressing (:class:`pod.dressing.models.Dressing`): The dressing object.
        ffmpeg_dressing_input (str): Source file for encoding.

    Returns:
        command (str): params for the ffmpeg command.
    """
    command = ""
    if dressing.watermark:
        command += ffmpeg_dressing_input % {"input": dressing.watermark.file.path}
    if dressing.opening_credits:
        command += ffmpeg_dressing_input % {
            "input": os.path.join(
                settings.MEDIA_ROOT, str(dressing.opening_credits.video)
            )
        }
    if dressing.ending_credits:
        command += ffmpeg_dressing_input % {
            "input": os.path.join(settings.MEDIA_ROOT, str(dressing.ending_credits.video))
        }
    return command


def get_dressings(user, accessgroup_set) -> list:
    """
    Return the list of dressings that the user can use.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object.
        accessgroup_set (:class:`pod.authentication.models.AccessGroup`): User acess groups.

    Returns:
        dressings (list): list of dressings.
    """
    dressings = Dressing.objects.filter(
        Q(owners=user) | Q(users=user) | Q(allow_to_groups__in=accessgroup_set)
    ).distinct()
    return dressings
