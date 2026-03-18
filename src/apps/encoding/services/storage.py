import os
import uuid


def get_storage_path_video(instance, filename: str) -> str:
    """
    Generates an optimized, user-independent storage path.
    Format: videos/<first_2_chars>/<next_2_chars>/<uuid>.<ext>
    Example: videos/a1/b2/a1b2c3d4e5f6...mp4
    """
    ext = filename.split(".")[-1].lower()

    file_uuid = uuid.uuid4().hex

    folder_level_1 = file_uuid[:2]
    folder_level_2 = file_uuid[2:4]
    new_filename = f"{file_uuid}.{ext}"

    return os.path.join("videos", folder_level_1, folder_level_2, new_filename)


def get_storage_path_image(instance, filename: str) -> str:
    """
    Generates an optimized, user-independent storage path.
    Format: thumbnails/<first_2_chars>/<next_2_chars>/<uuid>.<ext>
    Example: thumbnails/a1/b2/a1b2c3d4e5f6...mp4
    """
    ext = filename.split(".")[-1].lower()
    file_uuid = uuid.uuid4().hex

    return os.path.join("thumbnails", file_uuid[:2], file_uuid[2:4], f"{file_uuid}.{ext}")
