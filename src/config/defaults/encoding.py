"""
Esup-Pod - Encoding defaults.
Source of truth for default values for Encoding app.
"""

# Quota
USER_QUOTA_SIZE_GB = 5

# Video Storage
VIDEOS_DIR = "videos"
THUMBNAILS_DIR = "thumbnails"

# Upload
MAX_UPLOAD_SIZE_GB = 1
ALLOWED_EXTENSIONS = (
    "3gp",
    "avi",
    "divx",
    "flv",
    "m2p",
    "m4v",
    "mkv",
    "mov",
    "mp4",
    "mpeg",
    "mpg",
    "mts",
    "wmv",
    "mp3",
    "ogg",
    "wav",
    "wma",
    "webm",
    "ts",
)
VIDEO_REQUIRED_FIELDS = []

# Webhook behavior
KEEP_SOURCE_FILE = True
