from django.template import Library

from pod.video.models import Video

from ..utils import user_has_favorite_video, get_number_favorites

register = Library()


@register.simple_tag(takes_context=True, name="is_favorite")
def is_favorite(context: dict, video: Video) -> bool:
    """
    Template tag to check if the user has this video as favorite.

    Args:
        context (dict): The template context dictionary
        video (:class:`pod.video.models.Video`): The video entity to check

    Returns:
        bool: True if the user has the video as favorite, False otherwise
    """
    request = context["request"]
    if not request.user.is_authenticated:
        return False
    return user_has_favorite_video(request.user, video)


@register.simple_tag(name="number_favorites")
def number_favorites(video: Video) -> int:
    """
    Template tag to get the favorite number.

    Args:
        video (:class:`pod.video.models.Video`): The video entity

    Returns:
        int: The video favorite number
    """
    return get_number_favorites(video)
