"""
Video core services.

Exposes configuration values and constants for the video app.
Configuration is sourced from VideoSettings (conf.py) and EncodingSettings, constants from constants.py.
"""

from src.apps.encoding.constants import ENCODING_CHOICES, FORMAT_CHOICES
from ..conf import video_settings
from src.apps.encoding.conf import encoding_settings
from ..constants import (
    ALL_LANG_CHOICES,
    CURSUS_CODES,
    LANG_CHOICES,
    NOTES_STATUS,
    PREF_LANG_CHOICES,
    SOCIAL_SHARE,
)

# --- Storage ---
VIDEOS_DIR = encoding_settings.videos_dir
THUMBNAILS_DIR = encoding_settings.thumbnails_dir

# --- Upload ---
VIDEO_MAX_UPLOAD_SIZE = encoding_settings.max_upload_size_gb
VIDEO_ALLOWED_EXTENSIONS = encoding_settings.allowed_extensions
VIDEO_REQUIRED_FIELDS = encoding_settings.video_required_fields

# --- Encoding / FFmpeg ---
FFMPEG_CMD = encoding_settings.ffmpeg_cmd
FFPROBE_CMD = encoding_settings.ffprobe_cmd
FFMPEG_CRF = encoding_settings.ffmpeg_crf
FFMPEG_NB_THREADS = encoding_settings.ffmpeg_nb_threads
FFPROBE_GET_INFO = encoding_settings.ffprobe_get_info
CHUNK_SIZE = encoding_settings.chunk_size

# --- Feature Flags ---
USE_STATS_VIEW = video_settings.use_stats_view
VIEW_STATS_AUTH = video_settings.view_stats_auth
USER_VIDEO_CATEGORY = video_settings.user_video_category
WEBTV_MODE = video_settings.webtv_mode
USE_DUPLICATE = video_settings.use_duplicate
USE_CUT = video_settings.use_cut
ALLOW_AUTHENTICATED_UPLOAD = video_settings.allow_authenticated_upload

# --- Quota / Licensing ---
USER_QUOTA_SIZE = encoding_settings.user_quota_size_gb
DEFAULT_LICENSE = video_settings.default_license
CHANNEL_MODE = video_settings.channel_mode

# --- UI / Display ---
HIDE_USER_FILTER = video_settings.hide_user_filter
HIDE_TAGS = video_settings.hide_tags
FORCE_LOWERCASE_TAGS = video_settings.force_lowercase_tags
MAX_TAG_LENGTH = video_settings.max_tag_length
NUMBER_TAGS_CLOUD = video_settings.number_tags_cloud
HIDE_SHARE = video_settings.hide_share
HIDE_DISCIPLINES = video_settings.hide_disciplines
HIDE_CURSUS = video_settings.hide_cursus
HIDE_TYPES = video_settings.hide_types
RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY = video_settings.restrict_edit_to_staff
HOMEPAGE_SHOWS_PASSWORDED = video_settings.homepage_shows_passworded

# --- Cache ---
CACHE_VIDEO_DEFAULT_TIMEOUT = video_settings.cache_timeout
