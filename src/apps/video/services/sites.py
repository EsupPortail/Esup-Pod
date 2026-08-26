"""
Esup-Pod - Site assignment utilities.
"""

from django.contrib.sites.models import Site
from django.conf import settings


def assign_default_site(video):
    """
    Assigns a default site to a video if none is set.
    """

    if video.sites.exists():
        return video

    site = None

    # Preferred: use SITE_ID if defined
    site_id = getattr(settings, "SITE_ID", None)
    if site_id:
        site = Site.objects.filter(id=site_id).first()

    # Fallback: current site
    if site is None:
        site = Site.objects.get_current()

    if site:
        video.sites.add(site)

    return video
