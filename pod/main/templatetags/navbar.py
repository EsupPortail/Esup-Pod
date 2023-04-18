from django.template import Library
from django.contrib.auth.models import User

from pod.main.context_processors import RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY, \
    RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY, \
    USE_MEETING

# from django.utils.safestring import mark_safe
register = Library()


@register.simple_tag(takes_context=True, name="show_video_buttons")
def show_video_buttons(context, user: User):
    return (not RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY) \
        or (RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and user.is_staff)


@register.simple_tag(takes_context=True, name="show_meeting_button")
def show_meeting_button(context, user: User):
    return ((not RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY)
            or (RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY and user.is_staff)) \
        and USE_MEETING
