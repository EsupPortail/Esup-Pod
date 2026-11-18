"""Esup-Pod Live cache compatibility and configuration guidance."""

from django.core.cache import caches
from django.core.cache.backends.dummy import DummyCache
from django.core.cache.backends.locmem import LocMemCache
from django.utils.translation import gettext_lazy as _

SHARED_LIVE_CACHE_HELP = _(
    "As in the standard Esup-Pod configuration, CACHES['default'] must use the "
    "same Redis on all frontends to share Live state."
)

INCOMPATIBLE_LIVE_CACHE_WARNING = _(
    "The cache CACHES['default'] must be shared to add or change a secondary "
    "runner manager. Existing assignments are preserved."
)


def has_incompatible_live_cache() -> bool:
    """Detect local or dummy caches without claiming that Redis sharing is verified."""
    return isinstance(caches["default"], (LocMemCache, DummyCache))
