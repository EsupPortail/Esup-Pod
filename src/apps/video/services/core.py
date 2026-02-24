"""
Video core services.

Exposes configuration values and constants for the video app.
Configuration is sourced from VideoConfig (conf.py), constants from constants.py.
"""

from ..conf import video_settings
from ..constants import (
    ALL_LANG_CHOICES,
    CURSUS_CODES,
    ENCODING_CHOICES,
    FORMAT_CHOICES,
    LANG_CHOICES,
    NOTES_STATUS,
    PREF_LANG_CHOICES,
    SOCIAL_SHARE,
)

# --- Re-export constants for backward compatibility ---
__all__ = [
    # Constants
    "ALL_LANG_CHOICES",
    "PREF_LANG_CHOICES",
    "LANG_CHOICES",
    "FORMAT_CHOICES",
    "ENCODING_CHOICES",
    "NOTES_STATUS",
    "CURSUS_CODES",
    "SOCIAL_SHARE",
    # Config values (from VideoConfig)
    "VIDEOS_DIR",
    "THUMBNAILS_DIR",
    "VIDEO_ALLOWED_EXTENSIONS",
    "VIDEO_MAX_UPLOAD_SIZE",
    "VIDEO_REQUIRED_FIELDS",
    "FFMPEG_CMD",
    "FFPROBE_CMD",
    "FFMPEG_CRF",
    "FFMPEG_NB_THREADS",
    "FFPROBE_GET_INFO",
    "CHUNK_SIZE",
    "USE_STATS_VIEW",
    "VIEW_STATS_AUTH",
    "CACHE_VIDEO_DEFAULT_TIMEOUT",
    "USER_VIDEO_CATEGORY",
    "HIDE_USER_FILTER",
    "RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY",
    "HIDE_TAGS",
    "FORCE_LOWERCASE_TAGS",
    "MAX_TAG_LENGTH",
    "NUMBER_TAGS_CLOUD",
    "HIDE_SHARE",
    "HIDE_DISCIPLINES",
    "HIDE_CURSUS",
    "HIDE_TYPES",
    "WEBTV_MODE",
    "ALLOW_AUTHENTICATED_UPLOAD",
    "USER_QUOTA_SIZE",
    "DEFAULT_LICENSE",
    "CHANNEL_MODE",
    "HOMEPAGE_SHOWS_PASSWORDED",
    "USE_DUPLICATE",
    "USE_CUT",
    "USE_TRANSCRIPTION",
    "TRANSCRIPTION_MODEL_PARAM",
    "TRANSCRIPTION_TYPE",
    "THIRD_PARTY_APPS",
    "USE_PODFILE",
    "DEFAULT_DC_COVERAGE",
    "DEFAULT_DC_RIGHTS",
    "TEMPLATE_VISIBLE_SETTINGS",
    "DEFAULT_THUMBNAIL",
    "DEFAULT_TYPE_ID",
]

# --- Storage ---
VIDEOS_DIR = video_settings.videos_dir
THUMBNAILS_DIR = video_settings.thumbnails_dir

# --- Upload ---
VIDEO_MAX_UPLOAD_SIZE = video_settings.max_upload_size_gb
VIDEO_ALLOWED_EXTENSIONS = video_settings.allowed_extensions
VIDEO_REQUIRED_FIELDS = video_settings.video_required_fields

# --- Encoding / FFmpeg ---
FFMPEG_CMD = video_settings.ffmpeg_cmd
FFPROBE_CMD = video_settings.ffprobe_cmd
FFMPEG_CRF = video_settings.ffmpeg_crf
FFMPEG_NB_THREADS = video_settings.ffmpeg_nb_threads
FFPROBE_GET_INFO = video_settings.ffprobe_get_info
CHUNK_SIZE = video_settings.chunk_size

# --- Feature Flags ---
USE_STATS_VIEW = video_settings.use_stats_view
VIEW_STATS_AUTH = video_settings.view_stats_auth
USER_VIDEO_CATEGORY = video_settings.user_video_category
WEBTV_MODE = video_settings.webtv_mode
USE_DUPLICATE = video_settings.use_duplicate
USE_CUT = video_settings.use_cut
ALLOW_AUTHENTICATED_UPLOAD = video_settings.allow_authenticated_upload

# --- Quota / Licensing ---
USER_QUOTA_SIZE = video_settings.user_quota_size_gb
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

# --- Transcription ---
USE_TRANSCRIPTION = video_settings.use_transcription
TRANSCRIPTION_MODEL_PARAM = video_settings.transcription_model_param
TRANSCRIPTION_TYPE = video_settings.transcription_type

# --- Third Party & Plugins ---
THIRD_PARTY_APPS = video_settings.third_party_apps
USE_PODFILE = video_settings.use_podfile

# --- Metadata (Dublin Core) ---
DEFAULT_DC_COVERAGE = video_settings.default_dc_coverage
DEFAULT_DC_RIGHTS = video_settings.default_dc_rights
TEMPLATE_VISIBLE_SETTINGS = video_settings.template_visible_settings

# --- Media Defaults ---
DEFAULT_THUMBNAIL = video_settings.default_thumbnail
DEFAULT_TYPE_ID = video_settings.default_type_id
