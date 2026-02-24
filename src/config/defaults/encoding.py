"""
Encoding defaults.
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

# Encoding / FFmpeg
FFMPEG_CMD = "ffmpeg"
FFPROBE_CMD = "ffprobe"
FFMPEG_CRF = 20
FFMPEG_NB_THREADS = "slow"
FFPROBE_GET_INFO = "high"
CHUNK_SIZE = 100000