from django.template import Library

from pod.video.models import Video

from ..utils import user_has_favorite_video, get_number_favorites

register = Library()


@register.simple_tag(takes_context=True, name="is_favorite")
def is_favorite(context, video: Video):
    request = context["request"]
    return user_has_favorite_video(request.user, video)

@register.simple_tag(name="number_favorites")
def number_favorites(video: Video):
    return get_number_favorites(video)