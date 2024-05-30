"""Template tags for the AI enhancement app."""

from django.conf import settings
from django.template import Library


from pod.ai_enhancement.utils import (
    enhancement_is_ready as eir,
    enhancement_is_already_asked as eia,
)
from pod.video.models import Video


USE_AI_ENHANCEMENT = getattr(settings, "USE_AI_ENHANCEMENT", False)
AI_ENHANCEMENT_TO_STAFF_ONLY = getattr(settings, "AI_ENHANCEMENT_TO_STAFF_ONLY", True)

register = Library()


@register.simple_tag(takes_context=True, name="user_can_enhance_video")
def user_can_enhance_video(context: dict, video: Video) -> bool:
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
    if (
        request.user.is_authenticated
        and AI_ENHANCEMENT_TO_STAFF_ONLY
        and request.user.is_staff is False
    ):
        return False
    return (request.user.is_staff or request.user.is_superuser) and USE_AI_ENHANCEMENT


@register.simple_tag(takes_context=True, name="enhancement_is_ready")
def enhancement_is_ready(context: dict, video: Video) -> bool:
    """
    Template tag used to check if the enhancement of a specific video is ready.

    Args:
        context (dict): The context.
        video (:class:`pod.video.models.Video`): The specific video.

    Returns:
        bool: `True` if the enhancement is ready. `False` otherwise.
    """
    request = context["request"]
    if not request.user.is_authenticated:
        return False
    return eir(video) and USE_AI_ENHANCEMENT and user_can_enhance_video(context, video)


@register.simple_tag(takes_context=True, name="enhancement_is_already_asked")
def enhancement_is_already_asked(context: dict, video: Video) -> bool:
    """
    Template tag used to check if the enhancement of a specific video is already asked.

    Args:
        context (dict): The context.
        video (:class:`pod.video.models.Video`): The specific video.

    Returns:
        bool: `True` if the enhancement is already asked. `False` otherwise.
    """
    request = context["request"]
    if not request.user.is_authenticated:
        return False
    return (
        eia(video)
        and USE_AI_ENHANCEMENT
        and user_can_enhance_video(context, video)
        and not eir(video)
    )
