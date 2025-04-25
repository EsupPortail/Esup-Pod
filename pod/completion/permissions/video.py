from functools import wraps
from django.contrib import messages
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext as _
from pod.video.models import Video


def has_video_rights(permissions: list[str], message: str, prefetch_callback=None):
    """Check the current user's rights on a certain video."""

    def decorator(func):
        @wraps(func)
        def wrapper(request, slug: str, *args, **kwargs):
            current_user = request.user
            sites = get_current_site(request)
            queryset = Video.objects
            if prefetch_callback is not None:
                queryset = prefetch_callback(slug, current_user, sites)

            video = queryset.filter(slug=slug, sites=sites).first()
            if video is None:
                raise Http404("Video object not found.")

            is_one_of_additional_owners = current_user in video.additional_owners.all()
            has_permission = current_user.has_perms(permissions)
            is_owner_or_superuser = (
                current_user == video.owner or current_user.is_superuser
            )
            if not any(
                (is_owner_or_superuser, is_one_of_additional_owners, has_permission)
            ):
                messages.add_message(request, messages.ERROR, _(message))
                raise PermissionDenied(
                    _(f"{func.__name__}: Permission denied for user {current_user.pk}.")
                )

            return func(request, slug, video, *args, **kwargs)

        return wrapper

    return decorator
