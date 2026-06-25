"""
Esup-Pod - Base Respite model.

This is just a proof of concept, not intented to be used in production.
We invite you to use this as a starting point to establish your own model.
"""

import json

from pod.video.models import Video


def calcul(parameters, dry_mode: bool = True):
    """Calculate the number of days to add to date_delete"""

    # id: Id of the video (int)
    # title: Title of the video (string)
    # view_count: count the views of the video (int)
    # view_count_year: Views during the last year (int))
    # is_draft: Tell if it is in draft or not (bool)
    # is_restricted: Tell if video is restricted or not (bool)
    # date_added: upload date of the video (datetime)
    # days_on_platform: number of days on the platforme (int)
    # date_delete: scheduled date of suppression (datetime.date)
    # description: description of the video (string)
    # channels: list of channels where the video is (list)
    # nb_fav: number of favorite the video belong (int)
    # nb_comment: amount of comment on the video (int)
    # duration: 'duration of the video in sec (int)
    # disciplines: Video disciplines (list)
    # type: Video type (Type)
    # themes: themes of the video (list)
    # owner: owner of the video (User)
    # additional_owners: Additional owner of the video (list)
    # categories: categories of the video (list)
    if dry_mode:
        print(
            "Compute delete respite for video %s - %s"
            % (parameters["id"], parameters["title"])
        )
    print(json.dumps(parameters, sort_keys=True, indent=2, default=str))
    return 1


def can_video_be_archived(vid: Video):
    """Checks if a video can be archived"""
    return True
