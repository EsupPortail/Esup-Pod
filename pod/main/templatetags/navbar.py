"""Functions useful for the navigation bar."""
from django.template import Library

from pod.main.utils import get_number_playlist_for_user, get_number_video_for_user
from pod.playlist.context_processors import USE_PLAYLIST

# from django.utils.safestring import mark_safe
register = Library()


@register.simple_tag(takes_context=True, name="show_video_buttons")
def show_video_buttons(context):
    """Show 'Add video' buttons."""
    request = context["request"]
    return (not context["RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY"]) or (
        context["RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY"] and request.user.is_staff
    )


@register.simple_tag(takes_context=True, name="show_meeting_button")
def show_meeting_button(context):
    """Show 'Add meeting' button."""
    request = context["request"]
    return (
        (not context["RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY"])
        or (
            context["RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY"]
            and request.user.is_staff
        )
    ) and context["USE_MEETING"]


@register.simple_tag(name="show_stats")
def show_stats(user):
    return (get_number_video_for_user(user) > 0) or (
        get_number_playlist_for_user(user) > 0 and USE_PLAYLIST
    )


@register.simple_tag(name="get_number_video_user")
def get_number_video_user(user):
    return get_number_video_for_user(user)


@register.simple_tag(name="get_number_playlist_user")
def get_number_playlist_user(user):
    return get_number_playlist_for_user(user)


@register.simple_tag(takes_context=True, name="show_import_video_button")
def show_import_video_button(context):
    """Show 'Import video/External videos' button."""
    request = context["request"]
    return (
        (not context["RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY"])
        or (
            context["RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY"]
            and request.user.is_staff
        )
    ) and context["USE_IMPORT_VIDEO"]
