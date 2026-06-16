"""
Esup-Pod - Completion default configuration.
"""

from django.utils.translation import gettext_lazy as _
# Contributor roles (can be overridden by the instance)
ROLE_CHOICES = (
    ("actor", _("Actor")),
    ("author", _("Author")),
    ("consultant", _("Consultant")),
    ("contributor", _("Contributor")),
    ("director", _("Director")),
    ("speaker", _("Speaker")),
    ("technician", _("Technician")),
    ("voice-over", _("Voice-over")),
)

# Subtitle track types
KIND_CHOICES = (
    ("subtitles", _("Subtitles")),
    ("captions", _("Captions")),
)

# Default track language
DEFAULT_LANG_TRACK = "fr"

# Enable automatic conversion of URLs into links in overlays
LINK_SUPERPOSITION = False

# Enable or disable the Speakers module
USE_SPEAKER = False

# Make the first name of speakers mandatory
REQUIRED_SPEAKER_FIRSTNAME = True

