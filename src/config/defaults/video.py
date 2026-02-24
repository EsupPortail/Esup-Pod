"""
Video defaults.
Source of truth for default values for Video app.
"""

DEFAULT_LICENSE = ""
# Feature Flags
USE_STATS_VIEW = False
VIEW_STATS_AUTH = False
USER_VIDEO_CATEGORY = False
WEBTV_MODE = False
USE_DUPLICATE = False
USE_CUT = False
ALLOW_AUTHENTICATED_UPLOAD = True
CHANNEL_MODE = False

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
CACHE_TIMEOUT = 600  # TODO A voir quand il y aura redis
