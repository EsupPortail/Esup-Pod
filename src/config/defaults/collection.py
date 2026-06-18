"""
Esup-Pod - Collection defaults.
Source of truth for default values for the Collection app.
"""

# 1. Channel-related flags
USE_CHANNELS = True
OWNER_CAN_MANAGE_CHANNELS = True
USER_CAN_CREATE_CHANNEL = True
CAN_CHANGE_CHANNEL_OWNER = False
DEFAULT_CHANNEL_IMAGE = "img/default_channel.svg"
DEFAULT_CHANNEL_BANNER = "img/default_banner.svg"

# 2. Theme/Category-related flags
USE_CATEGORIES = True
THEME_MANDATORY = False
MAX_THEME_DEPTH = 3
SHOW_EMPTY_THEMES = True
OWNER_CAN_MANAGE_THEMES = False

# 3. Playlist-related flags
USE_PLAYLISTS = True
PLAYLIST_MAX_VIDEOS = 100
ALLOW_PUBLIC_PLAYLISTS = True

# 4. Favorite-related flags
USE_FAVORITES = True

# 5. Global Visibility flags
DEFAULT_VISIBILITY = "PUBLIC"  # Choices: PUBLIC, AUTHENTICATED, PRIVATE
USE_PASSWORD_PROTECTION = True

# 6. Pagination & Others
COLLECTIONS_PER_PAGE = 20
DEFAULT_KIND = "CHANNEL"
PERMITTED_KINDS = ["CHANNEL", "PLAYLIST", "THEME", "FAVORITES"]
DEFAULT_COLLECTION_ORDER_FIELD = "-created_at"
