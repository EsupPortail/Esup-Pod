import os
import uuid
from django.utils.text import slugify
from src.apps.video.services.core import VIDEOS_DIR, THUMBNAILS_DIR


def get_storage_path_video(instance, filename: str) -> str:
    """
    Calcule le chemin de stockage : videos/<hash_user>/<slug>.<ext>
    """
    ext = filename.split(".")[-1]
    user_partition = slugify(instance.owner.username)
    filename = f"{instance.slug}.{ext}"
    return os.path.join(VIDEOS_DIR, user_partition, filename)


def get_storage_path_image(instance, filename: str) -> str:
    ext = filename.split(".")[-1]
    return os.path.join(THUMBNAILS_DIR, f"{instance.slug}_{uuid.uuid4().hex[:6]}.{ext}")
