"""
Esup-Pod - Completion default configuration.
"""

# Contributor roles (can be overridden by the instance)
ROLE_CHOICES = (
    ("actor", "Actor"),
    ("author", "Author"),
    ("consultant", "Consultant"),
    ("contributor", "Contributor"),
    ("director", "Director"),
    ("speaker", "Speaker"),
    ("technician", "Technician"),
    ("voice-over", "Voice-over"),
)

# Subtitle track types
KIND_CHOICES = (
    ("subtitles", "Subtitles"),
    ("captions", "Captions"),
)

# Default track language
DEFAULT_LANG_TRACK = "fr"

# Enable automatic conversion of URLs into links in overlays
LINK_SUPERPOSITION = False

# Enable voice recognition model enrichment (Kaldi/VOSK)
ACTIVE_MODEL_ENRICH = False

# Enable or disable the Speakers module
USE_SPEAKER = False

# Make the first name of speakers mandatory
REQUIRED_SPEAKER_FIRSTNAME = True

# --- Transcription settings (only if ACTIVE_MODEL_ENRICH = True) ---
TRANSCRIPTION_TYPE = "WHISPER"
TRANSCRIPTION_MODEL_PARAM = {}
MODEL_COMPILE_DIR = ""
