"""Functions useful for the navigation bar."""
from django.template import Library

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
