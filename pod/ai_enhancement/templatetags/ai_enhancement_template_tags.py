"""Template tags for the AI enhancement app."""

from django.conf import settings
from django.template import Library


from pod.ai_enhancement.utils import (
    enrichment_is_ready as eir,
    enrichment_is_already_asked as eia,
)
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


@register.simple_tag(takes_context=True, name="enrichment_is_ready")
def enrichment_is_ready(context: dict, video: Video) -> bool:
    """
    Template tag used to check if the enrichment of a specific video is ready.

    Args:
        context (dict): The context.
        video (:class:`pod.video.models.Video`): The specific video.

    Returns:
        bool: `True` if the enrichment is ready. `False` otherwise.
    """
    request = context["request"]
    if not request.user.is_authenticated:
        return False
    return eir(video) and USE_AI_ENHANCEMENT and user_can_enrich_video(context, video)


@register.simple_tag(takes_context=True, name="enrichment_is_already_asked")
def enrichment_is_already_asked(context: dict, video: Video) -> bool:
    """
    Template tag used to check if the enrichment of a specific video is already asked.

    Args:
        context (dict): The context.
        video (:class:`pod.video.models.Video`): The specific video.

    Returns:
        bool: `True` if the enrichment is already asked. `False` otherwise.
    """
    request = context["request"]
    if not request.user.is_authenticated:
        return False
    return eia(video) and USE_AI_ENHANCEMENT and user_can_enrich_video(context, video) and not eir(video)
