"""
Esup-Pod - Video views.
"""

from .VideoViewSet import VideoViewSet  # noqa: F401
from .SubtitleViewSet import SubtitleViewSet  # noqa: F401
from .CommentViewSet import CommentViewSet  # noqa: F401
from .DisciplineViewSet import DisciplineViewSet  # noqa: F401
from .TagViewSet import TagViewSet  # noqa: F401
from .TypeViewSet import TypeViewSet  # noqa: F401
from .HyperlinkViewSet import VideoHyperlinkViewSet  # noqa: F401

__all__ = [
    "VideoViewSet",
    "SubtitleViewSet",
    "CommentViewSet",
    "DisciplineViewSet",
    "TagViewSet",
    "TypeViewSet",
    "VideoHyperlinkViewSet",
]
