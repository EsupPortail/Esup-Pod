import os
import uuid
from django.utils.text import slugify
from src.apps.encoding.conf import encoding_settings


def get_storage_path_video(instance, filename: str) -> str:
    """
    Calcule le chemin de stockage : videos/<hash_user>/<slug>.<ext>
    """
    ext = filename.split(".")[-1]
    user_partition = slugify(instance.owner.username)
    filename = f"{instance.slug}.{ext}"
    return os.path.join(encoding_settings.videos_dir, user_partition, filename)


def get_storage_path_image(instance, filename: str) -> str:
    ext = filename.split(".")[-1]
    return os.path.join(
        encoding_settings.thumbnails_dir, f"{instance.slug}_{uuid.uuid4().hex[:6]}.{ext}"
    )
