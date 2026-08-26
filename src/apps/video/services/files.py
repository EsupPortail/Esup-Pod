"""
Esup-Pod - Video file utilities.
"""

import shutil
import os


def duplicate_source_file(video_id, src_path, original_name):
    """
    Physically duplicates a video file on disk.

    Copies the file at src_path into the same directory, prefixed with
    the new video_id to avoid name collisions.

    Returns the absolute path of the newly created file.
    """
    base_dir = os.path.dirname(src_path)
    filename = os.path.basename(src_path)
    new_filename = f"{video_id}_{filename}"
    new_path = os.path.join(base_dir, new_filename)

    # original_name is the relative path stored in DB (e.g. video/sources/filename.mp4)
    new_name = os.path.join(os.path.dirname(original_name), new_filename)

    shutil.copy2(src_path, new_path)
    return new_name
