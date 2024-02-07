"""Template tags for the AI enhancement app."""

from django.conf import settings
from django.template import Library


from pod.video.models import Video


USE_AI_ENHANCEMENT = getattr(settings, "USE_AI_ENHANCEMENT", True)


register = Library()


@register.simple_tag(takes_context=True, name="user_can_enrich_video")
def user_can_enrich_video(context: dict, video: Video) -> bool:
    """
    Template tag used to check if the user can enrich a specific video.

    Args:
        context (dict): The context.
        video (:class:`pod.video.models.Video`): The specific video.

    Returns:
        bool: `True` if the user can do it. `False` otherwise.
    """
    request = context["request"]
    if not request.user.is_authenticated:
        return False
    return (
        ((video.owner == request.user) or request.user.is_superuser or request.user in video.additional_owners.all())
        and USE_AI_ENHANCEMENT
    )
