"""
Esup-Pod - Video application URL configuration.
"""

from django.urls import path
from rest_framework.routers import SimpleRouter
from src.apps.video.views import (
    VideoViewSet,
    SubtitleViewSet,
    CommentViewSet,
    DisciplineViewSet,
    TagViewSet,
    TypeViewSet,
    VideoHyperlinkViewSet,
    UserMarkerTimeViewSet,
)
from src.apps.video.conf import video_settings

router = SimpleRouter()
router.register(r"videos", VideoViewSet, basename="video")
router.register(r"subtitles", SubtitleViewSet, basename="subtitle")
router.register(r"disciplines", DisciplineViewSet, basename="discipline")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"types", TypeViewSet, basename="type")


if video_settings.use_hyperlinks:
    router.register(
        r"video-hyperlinks", VideoHyperlinkViewSet, basename="video-hyperlink"
    )

urlpatterns = router.urls

if video_settings.use_hyperlinks:
    urlpatterns += [
        path(
            "hyperlink/<slug:video_slug>/hyperlinks/",
            VideoHyperlinkViewSet.as_view({"get": "list_hyperlinks"}),
            name="video-hyperlink-list",
        ),
        path(
            "hyperlink/<slug:video_slug>/hyperlinks/add/",
            VideoHyperlinkViewSet.as_view({"post": "add_hyperlink"}),
            name="video-hyperlink-add",
        ),
        path(
            "hyperlink/<slug:video_slug>/hyperlinks/<uuid:hyperlink_id>/",
            VideoHyperlinkViewSet.as_view(
                {
                    "delete": "delete_hyperlink",
                    "patch": "edit_hyperlink",
                    "put": "edit_hyperlink",
                }
            ),
            name="video-hyperlink-detail",
        ),
    ]

if video_settings.use_marker_time:
    urlpatterns += [
        path(
            "marker/<slug:video_slug>/",
            UserMarkerTimeViewSet.as_view({"get": "get_marker"}),
            name="marker-get",
        ),
        path(
            "marker/<slug:video_slug>/save/",
            UserMarkerTimeViewSet.as_view({"post": "save_marker"}),
            name="marker-save",
        ),
        path(
            "marker/<slug:video_slug>/reset/",
            UserMarkerTimeViewSet.as_view({"delete": "reset_marker"}),
            name="marker-reset",
        ),
    ]

if video_settings.active_video_comment:
    urlpatterns += [
        path(
            "comment/<slug:video_slug>/",
            CommentViewSet.as_view({"get": "list_comments"}),
            name="comment-list",
        ),
        path(
            "comment/<int:comment_id>/<slug:video_slug>/",
            CommentViewSet.as_view({"get": "detail_comment"}),
            name="comment-detail",
        ),
        path(
            "comment/add/<slug:video_slug>/",
            CommentViewSet.as_view({"post": "add_comment"}),
            name="comment-add-root",
        ),
        path(
            "comment/add/<slug:video_slug>/<int:comment_id>/",
            CommentViewSet.as_view({"post": "add_comment"}),
            name="comment-reply",
        ),
        path(
            "comment/del/<slug:video_slug>/<int:comment_id>/",
            CommentViewSet.as_view({"post": "delete_comment"}),
            name="comment-delete",
        ),
        path(
            "comment/vote/<slug:video_slug>/",
            CommentViewSet.as_view({"get": "get_user_votes"}),
            name="comment-user-votes",
        ),
        path(
            "comment/vote/<slug:video_slug>/<int:comment_id>/",
            CommentViewSet.as_view({"post": "toggle_vote"}),
            name="comment-toggle-vote",
        ),
    ]
