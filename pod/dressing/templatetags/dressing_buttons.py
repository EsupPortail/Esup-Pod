"""Template tags used for dressing application buttons."""

from django.template import Library

from ..models import Dressing
from ..utils import (
    user_can_edit_dressing,
    user_can_delete_dressing
)

register = Library()


@register.simple_tag(takes_context=True, name="can_edit_dressing")
def can_edit_dressing(context: dict, dressing: Dressing) -> bool:
    """
    Template tag to check if the user can edit a dressing.

    Args:
        context (dict): The template context dictionary
        dressing (:class:`pod.dressing.models.Dressing`): The dressing entity to check

    Returns:
        bool: `True` if the user can, `False` otherwise
    """
    return user_can_edit_dressing(context["request"], dressing)


@register.simple_tag(takes_context=True, name="can_delete_dressing")
def can_delete_dressing(context: dict, dressing: Dressing) -> bool:
    """
    Template tag to check if the user can delete a dressing.

    Args:
        context (dict): The template context dictionary
        dressing (:class:`pod.dressing.models.Dressing`): The dressing entity to check

    Returns:
        bool: `True` if the user can, `False` otherwise
    """
    return user_can_delete_dressing(context["request"], dressing)
