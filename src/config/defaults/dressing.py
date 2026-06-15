"""
Esup-Pod - Dressing default configuration.
"""

USE_DRESSING = True

# Allows standard users to create their own dressings.
# If False, only administrators can create them, users will only choose among the authorized ones.
ALLOW_USER_CUSTOM_DRESSING = True

# Maximum allowed size (in MB) for watermark image upload
MAX_WATERMARK_SIZE_MB = 5

# Maximum allowed duration (in seconds) for credits videos (opening/ending).
# Prevents using a full video as credits to bypass limits.
MAX_CREDITS_DURATION_SECONDS = 60

# Default values for the interface
DEFAULT_WATERMARK_OPACITY = 100
DEFAULT_WATERMARK_POSITION = "top_right"
