"""
Esup-Pod - Live application default configuration values.
"""

# --- Feature Flags ---
USE_LIVE = True
USE_LIVE_TRANSCRIPTION = False

# --- Access Control ---
AFFILIATION_EVENT = ("faculty", "employee", "staff")
EVENT_GROUP_ADMIN = "event admin"

# --- Timing ---
HEARTBEAT_DELAY = 45  # seconds

# --- Thumbnails ---
DEFAULT_EVENT_THUMBNAIL = "img/default-event.svg"
DEFAULT_THUMBNAIL = "img/default.svg"

# --- Email ---
EMAIL_ON_EVENT_SCHEDULING = False

# --- Transcription ---
LIVE_TRANSCRIPTIONS_FOLDER = "live_transcripts"

# --- Recording ---
DEFAULT_EVENT_PATH = ""
DEFAULT_EVENT_TYPE_ID = 1
