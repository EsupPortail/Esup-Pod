"""
Esup-Pod - Layout configuration settings.
"""

from django.conf import settings


class LayoutSettings:
    """Settings for the Layout application."""

    @property
    def use_layout_blocks(self) -> bool:
        """Return True if layout blocks are enabled."""
        return getattr(settings, "USE_LAYOUT_BLOCKS", True)


layout_settings = LayoutSettings()
