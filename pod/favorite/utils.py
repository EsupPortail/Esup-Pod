from django.contrib.auth.models import User
from django.db.models import Max

from .models import Favorite
from pod.video.models import Video


def user_has_favorite_video(user: User, video: Video) -> bool:
    """
    Know if user has the video in favorite.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user entity
        video (:class:`pod.video.models.Video`): The video entity

    Returns:
        bool: True if user has the video in favorite, False otherwise
    """
    return Favorite.objects.filter(owner=user, video=video).exists()


def user_add_or_remove_favorite_video(user: User, video: Video):
    """
    Add or remove the video in favorite list of the user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user entity
        video (:class:`pod.video.models.Video`): The video entity
    """
    if user_has_favorite_video(user, video):
        Favorite.objects.filter(owner=user, video=video).delete()
    else:
        Favorite.objects.create(owner=user, video=video, rank=get_next_rank(user))


def get_next_rank(user: User) -> int:
    """
    Get the next favorite rank for the user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user entity

    Returns:
        int: The next rank
    """
    last_rank = Favorite.objects.filter(owner=user).aggregate(Max('rank'))['rank__max']
    return last_rank + 1 if last_rank is not None else 1


def get_number_favorites(video: Video):
    return Favorite.objects.filter(video=video).count()


def get_all_favorite_videos_for_user(user: User) -> list:
    """
    Get all favorite videos for a specific user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user entity

    Returns:
        list(:class:`pod.video.models.Video`): The video list
    """
    favorite_id = Favorite.objects.filter(owner=user).values_list('video_id', flat=True)
    video_list = Video.objects.filter(id__in=favorite_id).extra(
        select={'rank': 'favorite_favorite.rank'},
        tables=['favorite_favorite'],
        where=[
            'favorite_favorite.video_id=video_video.id',
            'favorite_favorite.owner_id=%s'
        ],
        params=[user.id]
    )
    return video_list


def sort_videos_list(request, videos_list):
    """
    Return sorted videos list by specific column name and ascending or descending
    direction (boolean)
    """
    if request.GET.get('sort'):
        sort = request.GET.get('sort')
    else:
        sort = "rank"
    if not request.GET.get('sort_direction'):
        sort = '-' + sort
    videos_list = videos_list.order_by(sort)
    return videos_list.distinct()
