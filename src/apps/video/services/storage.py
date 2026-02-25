import os
import uuid
from django.utils.text import slugify
from src.apps.video.services.core import VIDEOS_DIR, THUMBNAILS_DIR
import shutil
from django.conf import settings


def get_storage_path_video(instance, filename: str) -> str:
    """
    Calculates the storage path: videos/<hash_user>/<slug>.<ext>
    """
    ext = filename.split(".")[-1]
    user_partition = slugify(instance.owner.username)
    filename = f"{instance.slug}.{ext}"
    return os.path.join(VIDEOS_DIR, user_partition, filename)


def get_storage_path_image(instance, filename: str) -> str:
    ext = filename.split(".")[-1]
    return os.path.join(THUMBNAILS_DIR, f"{instance.slug}_{uuid.uuid4().hex[:6]}.{ext}")


def move_video_files_to_new_owner(video, old_owner, new_owner):
    """
    Physically moves the video folder and updates the paths in the database.
    """
    old_hash = old_owner.owner.hashkey
    new_hash = new_owner.owner.hashkey
    if old_hash == new_hash:
        return
    video_folder_name = f"{video.id:04d}"
    old_base_path = os.path.join(settings.MEDIA_ROOT, "videos", old_hash, video_folder_name)
    new_user_path = os.path.join(settings.MEDIA_ROOT, "videos", new_hash)
    new_base_path = os.path.join(new_user_path, video_folder_name)
    if os.path.exists(old_base_path):
        os.makedirs(new_user_path, exist_ok=True)
        shutil.move(old_base_path, new_base_path)
    if video.video_file:
        video.video_file.name = video.video_file.name.replace(old_hash, new_hash)
    if video.thumbnail:
        video.thumbnail.name = video.thumbnail.name.replace(old_hash, new_hash)
    video.save(update_fields=['video_file', 'thumbnail'])
