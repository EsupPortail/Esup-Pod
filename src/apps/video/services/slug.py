"""
Esup-Pod - Video slug utilities.
"""

from src.apps.video.models import Video


def generate_unique_slug(base_slug: str) -> str:
    """
    Ensures slug uniqueness in DB.

    Appends an incrementing suffix (-1, -2, ...) until no existing Video
    matches the candidate slug.
    """
    slug = base_slug
    counter = 1
    while Video.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
