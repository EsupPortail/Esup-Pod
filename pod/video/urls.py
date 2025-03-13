"""Esup-Pod Video Urls."""

from django.conf import settings
from django.urls import include, path, re_path

from .views import (
    video,
    video_edit,
    video_add,
    video_delete,
    video_transcript,
    dashboard,
    bulk_update,
    video_notes,
    video_count,
    video_marker,
    video_version,
    get_categories_list,
    add_category,
    edit_category,
    delete_category,
    update_video_owner,
    filter_owners,
    filter_videos,
    PodChunkedUploadView,
    PodChunkedUploadCompleteView,
    stats_view,
    video_oembed,
    get_channels_for_specific_channel_tab,
    get_channel_tabs_for_navbar,
    get_comments,
    get_children_comment,
    get_theme_list_for_specific_channel,
    add_comment,
    delete_comment,
    vote_get,
    vote_post,
    video_edit_access_tokens,
)


app_name = "video"

urlpatterns = [
    # Manage video owner
    re_path(
        r"^updateowner/put/(?P<user_id>[\d]+)/$",
        update_video_owner,
        name="update_video_owner",
    ),
    path("updateowner/owners/", filter_owners, name="filter_owners"),
    re_path(
        r"^updateowner/videos/(?P<user_id>[\d]+)/$",
        filter_videos,
        name="filter_videos",
    ),
    path("add/", video_add, name="video_add"),
    path("edit/", video_edit, name="video_edit"),
    re_path(r"^edit/(?P<slug>[\-\d\w]+)/$", video_edit, name="video_edit"),
    re_path(
        r"^edit_access_tokens/(?P<slug>[\-\d\w]+)/$",
        video_edit_access_tokens,
        name="video_edit_access_tokens",
    ),
    re_path(
        r"^delete/(?P<slug>[\-\d\w]+)/$",
        video_delete,
        name="video_delete",
    ),
    re_path(
        r"^transcript/(?P<slug>[\-\d\w]+)/$",
        video_transcript,
        name="video_transcript",
    ),
    re_path(r"^notes/(?P<slug>[\-\d\w]+)/$", video_notes, name="video_notes"),
    re_path(r"^count/(?P<id>[\d]+)/$", video_count, name="video_count"),
    re_path(
        r"^marker/(?P<id>[\d]+)/(?P<time>[\d]+)/$", video_marker, name="video_marker"
    ),
    re_path(r"^version/(?P<id>[\d]+)/$", video_version, name="video_version"),
    re_path(
        "api/chunked_upload_complete/",
        PodChunkedUploadCompleteView.as_view(),
        name="api_chunked_upload_complete",
    ),
    re_path(
        "api/chunked_upload/",
        PodChunkedUploadView.as_view(),
        name="api_chunked_upload",
    ),
    path("dashboard/", dashboard, name="dashboard"),
    path("bulk_update/", bulk_update, name="bulk_update"),
]
# COMPLETION
urlpatterns += [
    path("completion/", include("pod.completion.urls", namespace="completion")),
]
# CHAPTER
urlpatterns += [
    path("chapter/", include("pod.chapter.urls", namespace="chapter")),
]

# DRESSING
urlpatterns += [
    path("dressing/", include("pod.dressing.urls", namespace="video_dressing")),
]

urlpatterns += [
    path("duplicate/", include("pod.duplicate.urls", namespace="duplicate")),
]

urlpatterns += [
    path("hyperlinks/", include("pod.hyperlinks.urls", namespace="hyperlinks")),
]

##
# OEMBED feature patterns
#
if getattr(settings, "OEMBED", False):
    urlpatterns += [
        re_path(r"^oembed/", video_oembed, name="video_oembed"),
    ]

# VIDEO CATEGORY
if getattr(settings, "USER_VIDEO_CATEGORY", False):
    urlpatterns += [
        path("categories/", get_categories_list, name="get_categories_list"),
        path("category/add/", add_category, name="add_category"),
        re_path(
            r"^category/edit/(?P<c_slug>[\-\d\w]+)/$", edit_category, name="edit_category"
        ),
        re_path(
            r"^category/delete/(?P<c_slug>[\-\d\w]+)/$",
            delete_category,
            name="delete_category",
        ),
    ]

if getattr(settings, "USE_STATS_VIEW", False):
    urlpatterns += [
        path("stats_view/", stats_view, name="video_stats_view"),
        re_path(
            r"^stats_view/(?P<slug>[-\w]+)/$",
            stats_view,
            name="video_stats_view",
        ),
        re_path(
            r"^stats_view/(?P<slug>[-\w]+)/(?P<slug_t>[-\w]+)/$",
            stats_view,
            name="video_stats_view",
        ),
    ]

# COMMENT and VOTE
if getattr(settings, "ACTIVE_VIDEO_COMMENT", False):
    urlpatterns += [
        re_path(
            r"^comment/(?P<video_slug>[\-\d\w]+)/$",
            get_comments,
            name="get_comments",
        ),
        re_path(
            r"^comment/(?P<comment_id>[\d]+)/(?P<video_slug>[\-\d\w]+)/$",
            get_children_comment,
            name="get_comment",
        ),
        re_path(
            r"^comment/add/(?P<video_slug>[\-\d\w]+)/$",
            add_comment,
            name="add_comment",
        ),
        re_path(
            r"^comment/add/(?P<video_slug>[\-\d\w]+)/(?P<comment_id>[\d]+)/$",
            add_comment,
            name="add_child_comment",
        ),
        re_path(
            r"^comment/del/(?P<video_slug>[\-\d\w]+)/(?P<comment_id>[\d]+)/$",
            delete_comment,
            name="delete_comment",
        ),
        re_path(
            r"^comment/vote/(?P<video_slug>[\-\d\w]+)/$",
            vote_get,
            name="get_votes",
        ),
        re_path(
            r"^comment/vote/(?P<video_slug>[\-\d\w]+)/(?P<comment_id>[\d]+)/$",
            vote_post,
            name="add_vote",
        ),
    ]

# NAVBAR
urlpatterns += [
    path("get-channel-tabs/", get_channel_tabs_for_navbar, name="get-channel-tabs"),
    path(
        "get-channels-for-specific-channel-tab/",
        get_channels_for_specific_channel_tab,
        name="get-channels-for-specific-channel-tab",
    ),
    path(
        "get-themes-for-specific-channel/<slug:slug>/",
        get_theme_list_for_specific_channel,
        name="get-themes-for-specific-channel",
    ),
]

# DIRECT ACCESS TO A VIDEO
urlpatterns += [
    re_path(r"^(?P<slug>[\-\d\w]+)/$", video, name="video"),
    re_path(
        r"^(?P<slug>[\-\d\w]+)/(?P<slug_private>[\-\d\w]+)/$",
        video,
        name="video_private",
    ),
]
