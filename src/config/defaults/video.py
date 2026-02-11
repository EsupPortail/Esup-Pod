"""
Video defaults.
Source of truth for default values for Video app.
"""

# Storage
VIDEOS_DIR = "videos"
THUMBNAILS_DIR = "thumbnails"

# Upload
MAX_UPLOAD_SIZE_GB = 1
DEFAULT_LICENSE = ""
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

# Feature Flags
USE_STATS_VIEW = False
VIEW_STATS_AUTH = False
USER_VIDEO_CATEGORY = False
WEBTV_MODE = False
USE_DUPLICATE = False
USE_CUT = False
ALLOW_AUTHENTICATED_UPLOAD = True
CHANNEL_MODE = False

# Quota
USER_QUOTA_SIZE_GB = 5

# UI / Display Flags
HIDE_USER_FILTER = False
HIDE_TAGS = False
FORCE_LOWERCASE_TAGS = True
MAX_TAG_LENGTH = 50
NUMBER_TAGS_CLOUD = 20
HIDE_SHARE = False
HIDE_DISCIPLINES = False
HIDE_CURSUS = False
HIDE_TYPES = False
RESTRICT_EDIT_TO_STAFF = False
HOMEPAGE_SHOWS_PASSWORDED = False

# Cache
CACHE_TIMEOUT = 600
