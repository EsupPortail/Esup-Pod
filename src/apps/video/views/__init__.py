"""
Esup-Pod - Video views.
"""

from .VideoViewSet import VideoViewSet
from .SubtitleViewSet import SubtitleViewSet
from .CommentViewSet import CommentViewSet
from .DisciplineViewSet import DisciplineViewSet
from .TagViewSet import TagViewSet

__all__ = [
    "VideoViewSet",
    "SubtitleViewSet",
    "CommentViewSet",
    "DisciplineViewSet",
    "TagViewSet",
]
