"""
Esup-Pod - Storage path helpers for models.
"""

import os
from django.template.defaultfilters import slugify


def get_upload_path_files(instance, filename) -> str:
    """
    Generate upload path for files to match V4 structure.
    Format: files/<user_hash>/slugified_filename.ext
    """
    user_rep = "anonymous"
    if instance.created_by:
        if hasattr(instance.created_by, "owner") and instance.created_by.owner:
            user_rep = instance.created_by.owner.hashkey
        else:
            user_rep = instance.created_by.username

    fname, dot, extension = filename.rpartition(".")
    try:
        fname.index("/")
        return os.path.join(
            "files",
            user_rep,
            "%s/%s.%s"
            % (
                os.path.dirname(fname),
                slugify(os.path.basename(fname)),
                extension,
            ),
        )
    except ValueError:
        return os.path.join("files", user_rep, "%s.%s" % (slugify(fname), extension))
