from pod.activitypub.models import ExternalVideo


def get_available_external_videos_filter(request=None):
    """Return the base filter to get the available external videos of the site."""

    return ExternalVideo.objects.filter()


def get_available_external_videos(request=None):
    """Get all external videos available."""
    return get_available_external_videos_filter(request).distinct()
