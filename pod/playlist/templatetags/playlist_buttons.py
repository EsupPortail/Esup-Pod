from django.template import Library

from ..models import Playlist

register = Library()


@register.simple_tag(takes_context=True, name="user_can_edit_or_remove")
def user_can_edit_or_remove(context: dict, playlist: Playlist) -> bool:
    request = context["request"]
    if not request.user.is_authenticated:
        return False
    return playlist.editable and (request.user == playlist.owner or request.user.is_staff)
