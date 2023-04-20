from django.template import Library

# from django.utils.safestring import mark_safe
register = Library()


@register.simple_tag(takes_context=True, name="show_video_buttons")
def show_video_buttons(context):
    request = context["request"]
    return (not context["RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY"]) or (
        context["RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY"] and request.user.is_staff
    )


@register.simple_tag(takes_context=True, name="show_meeting_button")
def show_meeting_button(context):
    request = context["request"]
    return (
        (not context["RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY"])
        or (
            context["RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY"]
            and request.user.is_staff
        )
    ) and context["USE_MEETING"]
