"""
Esup-Pod - Service for resolving legacy V4 collection links.
"""

from django.urls import reverse
from src.apps.collection.models import Channel, Theme


def resolve_legacy_v4_collection(old_id):
    """
    Identifies if an old V4 ID corresponds to a Channel or a Theme.
    Returns the new V5 URL if found, otherwise None.
    """
    channel = Channel.objects.filter(old_v4_id=old_id).first()
    if channel:
        return reverse("channel-detail", kwargs={"slug": channel.slug})
    theme = Theme.objects.filter(old_v4_id=old_id).first()
    if theme:
        return reverse("theme-detail", kwargs={"slug": theme.slug})

    return None
