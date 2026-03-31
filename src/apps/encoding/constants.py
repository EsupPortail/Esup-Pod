"""
Esup-Pod - Encoding app constants.

Static data (choices tuples) that are NOT configurable via environment variables.
"""

# --- Format Choices ---
FORMAT_CHOICES = (
    ("video/mp4", "video/mp4"),
    ("video/mp2t", "video/mp2t"),
    ("video/webm", "video/webm"),
    ("audio/mp3", "audio/mp3"),
    ("audio/wav", "audio/wav"),
    ("application/x-mpegURL", "application/x-mpegURL"),
)

# --- Encoding Choices ---
ENCODING_CHOICES = (
    ("audio", "audio"),
    ("360p", "360p"),
    ("480p", "480p"),
    ("720p", "720p"),
    ("1080p", "1080p"),
    ("playlist", "playlist"),
)
