"""
Esup-Pod - Video defaults.
Source of truth for default values for Video app.
"""

DEFAULT_LICENSE = ""
# Feature Flags
USE_STATS_VIEW = False
VIEW_STATS_AUTH = False
USER_VIDEO_CATEGORY = False
WEBTV_MODE = False
USE_DUPLICATE = False
USE_HYPERLINKS = False
USE_CUT = False
ALLOW_AUTHENTICATED_UPLOAD = True
CHANNEL_MODE = False
ACTIVE_VIDEO_COMMENT = True
USE_VIDEO_ACCESS_TOKEN = False
VIDEO_TOKEN_DEFAULT_VALIDITY_DAYS = 7
VIDEO_TOKEN_MAX_VALIDITY_DAYS = 365

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

USE_TRANSCRIPTION = False
TRANSCRIPTION_MODEL_PARAM = {}
TRANSCRIPTION_TYPE = "WHISPER"

THIRD_PARTY_APPS = []
USE_PODFILE = False

DEFAULT_DC_COVERAGE = "University name"
DEFAULT_DC_RIGHTS = "BY-NC-SA"

TEMPLATE_VISIBLE_SETTINGS = {
    "TITLE_ETB": "University name",
}

DEFAULT_THUMBNAIL = "img/default_thumbnail.svg"
DEFAULT_TYPE_ID = 1

ACCOMMODATION_YEARS = {}
DEFAULT_YEAR_DATE_DELETE = 2
DELETE_SOURCE_ON_VIDEO_DELETE = True

METADATA_LANGUAGES = [
    {"value": "fr", "label": "French"},
    {"value": "en", "label": "English"},
    {"value": "es", "label": "Spanish"},
    {"value": "de", "label": "German"},
    {"value": "it", "label": "Italian"},
]

# Subtitle languages choices
SUBTITLE_LANGUAGES = [
    {"value": "fr", "label": "French"},
    {"value": "en", "label": "English"},
    {"value": "es", "label": "Spanish"},
    {"value": "de", "label": "German"},
]
DEFAULT_SUBTITLE_LANGUAGE = "fr"

METADATA_LICENSES = [
    {"value": "CC-BY", "label": "Creative Commons BY"},
    {"value": "CC-BY-SA", "label": "Creative Commons BY-SA"},
    {"value": "CC-BY-NC", "label": "Creative Commons BY-NC"},
    {"value": "CC-BY-ND", "label": "Creative Commons BY-ND"},
    {"value": "COPYRIGHT", "label": "All rights reserved"},
]

METADATA_CURSUS = [
    {"value": "L1", "label": "Licence 1"},
    {"value": "L2", "label": "Licence 2"},
    {"value": "L3", "label": "Licence 3"},
    {"value": "M1", "label": "Master 1"},
    {"value": "M2", "label": "Master 2"},
    {"value": "D", "label": "Doctorate"},
    {"value": "0", "label": "Other"},
]
