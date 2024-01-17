"""Esup-Pod dressing utilities."""
import os
from .models import Dressing
from django.conf import settings
from django.db.models import Q


def get_position_value(position, height):
    """
    Obtain dimensions proportional to the video format.

    Args:
        position (str): proprerty "position" of the dressing object.
        height (str): height of the source video.

    Returns:
        str: params for the ffmpeg command.
    """
    height = str(float(height) * 0.05)
    if position == "top_right":
        return "overlay=main_w-overlay_w-" + height + ":" + height
    elif position == "top_left":
        return "overlay=" + height + ":" + height
    elif position == "bottom_right":
        return "overlay=main_w-overlay_w-" + height + ":main_h-overlay_h-" + height
    elif position == "bottom_left":
        return "overlay=" + height + ":main_h-overlay_h-" + height


def get_dressing_input(dressing, FFMPEG_DRESSING_INPUT):
    """
    Function to obtain the files necessary for encoding a dressed video.

    Args:
        dressing (:class:`pod.dressing.models.Dressing`): The dressing object.
        FFMPEG_DRESSING_INPUT (str): Source file for encoding.

    Returns:
        command (str): params for the ffmpeg command.
    """
    command = ""
    if dressing.watermark:
        command += FFMPEG_DRESSING_INPUT % {
            "input": os.path.join(settings.BASE_DIR, dressing.watermark.file.url[1:])
        }
    if dressing.opening_credits:
        command += FFMPEG_DRESSING_INPUT % {
            "input": os.path.join(
                settings.MEDIA_ROOT, str(dressing.opening_credits.video)
            )
        }
    if dressing.ending_credits:
        command += FFMPEG_DRESSING_INPUT % {
            "input": os.path.join(settings.MEDIA_ROOT, str(dressing.ending_credits.video))
        }
    return command


def get_dressings(user, accessgroup_set):
    """
    Function that returns the list of dressings that the user can use.

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
