"""Esup-Pod dressing utilities."""

import os
from .models import Dressing
from django.conf import settings
from django.db.models import Q


def get_dressing_input(dressing: Dressing, FFMPEG_DRESSING_INPUT: str) -> str:
    """
    Obtain the files necessary for encoding a dressed video.

    Args:
        dressing (:class:`pod.dressing.models.Dressing`): The dressing object.
        FFMPEG_DRESSING_INPUT (str): Source file for encoding.

    Returns:
        command (str): params for the ffmpeg command.
    """
    command = ""
    if dressing.get("watermark_path", "") != "":
        command += FFMPEG_DRESSING_INPUT % {"input": dressing["watermark_path"]}
    if dressing.get("opening_credits_video", "") != "":
        command += FFMPEG_DRESSING_INPUT % {
            "input": os.path.join(
                settings.MEDIA_ROOT, dressing["opening_credits_video"]
            )
        }
    if dressing.get("ending_credits_video", "") != "":
        command += FFMPEG_DRESSING_INPUT % {
            "input": os.path.join(settings.MEDIA_ROOT, dressing["ending_credits_video"])
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
