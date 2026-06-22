"""
Esup-Pod - Utility functions for storage path generation.

This module defines naming conventions for video, image, and other files stored on disk,
respecting the V4 directory structure for backward compatibility.
"""

import os
import uuid
import hashlib
from django.utils import timezone


def _hash_filename(filename: str) -> str:
    """
    Hash the filename to prevent predictability and obscure the physical file.
    Example: 8ab2c44298fc1c149afbf4c8996fb92427ae41e4.mp4
    """
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    file_uuid = uuid.uuid4().hex
    hashed_name = hashlib.sha1(f"{file_uuid}-{filename}".encode("utf-8")).hexdigest()
    return f"{hashed_name}.{ext}" if ext else hashed_name


def get_storage_path_video(instance, filename: str) -> str:
    """
    Generates the storage path for original video source files.
    Format: video/source/%Y/%m/%d/hash.ext
    """
    return os.path.join(
        "video", "source", timezone.now().strftime("%Y/%m/%d"), _hash_filename(filename)
    )


def get_storage_path_image(instance, filename: str) -> str:
    """
    Generates the storage path for video thumbnails and overview images.
    Format: video/thumbnails/%Y/%m/%d/hash.ext
    """
    return os.path.join(
        "video",
        "thumbnails",
        timezone.now().strftime("%Y/%m/%d"),
        _hash_filename(filename),
    )


def get_storage_path_encoded_video(instance, filename: str) -> str:
    """
    Generates the storage path for encoded videos.
    Format: video/encoded/%Y/%m/%d/hash.ext
    """
    return os.path.join(
        "video",
        "encoded",
        timezone.now().strftime("%Y/%m/%d"),
        _hash_filename(filename),
    )


def get_storage_path_transcript(instance, filename: str) -> str:
    """
    Generates the storage path for subtitles/transcripts files.
    Format: video/transcripts/%Y/%m/%d/hash.ext
    """
    return os.path.join(
        "video",
        "transcripts",
        timezone.now().strftime("%Y/%m/%d"),
        _hash_filename(filename),
    )


def get_storage_path_user_picture(instance, filename: str) -> str:
    """
    Generates the storage path for user profile pictures.
    Format: userpicture/%Y/%m/%d/hash.ext
    """
    return os.path.join(
        "userpicture", timezone.now().strftime("%Y/%m/%d"), _hash_filename(filename)
    )


def get_storage_path_collection_image(instance, filename: str) -> str:
    """
    Generates the storage path for collection logos and banners.
    Format: collection/images/%Y/%m/%d/hash.ext
    """
    return os.path.join(
        "collection",
        "images",
        timezone.now().strftime("%Y/%m/%d"),
        _hash_filename(filename),
    )


def get_storage_path_document(instance, filename: str) -> str:
    """
    Generates the storage path for completion documents attached to a video.
    Format: video/documents/%Y/%m/%d/hash.ext
    """
    return os.path.join(
        "video",
        "documents",
        timezone.now().strftime("%Y/%m/%d"),
        _hash_filename(filename),
    )
