from pod.video.models import Video


def calcul(parameters, dry_mode: bool = True):
    """Calculate the number of days to add to date_delete"""

    # id: Id of the video (int)
    # title: Title of the video (string)
    # view_count : count the views of the video (int)
    # view_count_year : Views during the last year)
    # is_draft : Tell if it is in draft or not (bool)
    # is_restricted : Tell if it is restricted or not (bool)
    # date_added': upload date of the video(datetime)
    # days_on_platform: number of days on the platforme (int)
    # date_delete: scheduled date of suppression (datetime.date)
    # description: description of the video (string)
    # nb_channel: count of the number of channel the video belong (int)
    # channel_list: list of channel for a video [array}
    # nb_fav: number of favorite the video belong (int)
    # nb_comment: amount of comment on the video (int)
    # duration_video: 'duration of the video in sec (int)
    # type_name_video : Video type (string)
    # type_id_video : Video type (id)
    # theme_list: themes of the video (array)
    # nb_theme: number of the video (int)
    # owner_video': owner of the video (string)
    # owner_video_additional: Additional owner of the video (array)
    # category_list: categories of the video (array)

    print(parameters)
    return 1


def can_video_be_archived(vid: Video):
    """Checks if a video can be archived"""
    return True
