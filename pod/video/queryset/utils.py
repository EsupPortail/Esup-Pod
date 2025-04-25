from django.db.models import Prefetch
from pod.video.models import Video
from pod.completion.models import Track


def prefetch_video_completion_hyperlink(slug: str, user, sites):
    """Prefetch related data for video completion hyperlink."""
    if user.is_staff:
        return Video.objects.prefetch_related(
            Prefetch("contributor_set", to_attr="list_contributor"),
            Prefetch("track_set", queryset=Track.objects.all().order_by("lang"), to_attr="list_track"),
            Prefetch("document_set", to_attr="list_document"),
            Prefetch("overlay_set", to_attr="list_overlay"),
            Prefetch("video_hyperlinks", to_attr="list_hyperlink"),
        )
    return Video.objects.prefetch_related(
        Prefetch("contributor_set", to_attr="list_contributor")
    )
