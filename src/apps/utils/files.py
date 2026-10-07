"""
Esup-Pod - File utility functions.
"""

import os

SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]


def safe_remove_file(field) -> None:
    """
    Safely deletes a file from disk if it exists.
    Handles ValueError when field is empty/null or path is invalid.
    """
    if field:
        try:
            if os.path.isfile(field.path):
                os.remove(field.path)
        except ValueError:
            pass


def resolve_file_field_image_url(file_field) -> str | None:
    """
    Returns the image URL for a given file field.

    If the field points to a .vtt storyboard file, it attempts to locate an existing image
    with a supported extension (.png, .jpg, .jpeg, .webp) alongside the .vtt file.
    """
    if not file_field or not hasattr(file_field, "url"):
        return None

    url = file_field.url
    if url and url.endswith(".vtt"):
        from pathlib import Path

        base_url = Path(url)
        base_name = Path(file_field.name)
        storage = file_field.storage

        for ext in SUPPORTED_IMAGE_EXTENSIONS:
            if storage.exists(str(base_name.with_suffix(ext))):
                return str(base_url.with_suffix(ext))

        return str(base_url.with_suffix(".png"))

    return url
