from django.conf import settings
from django.conf.urls import url
from django.urls import include, path

from .views import video
from .views import video_edit
from .views import video_add
from .views import video_delete

from .views import my_videos
from .views import video_notes
from .views import video_xhr
from .views import video_count, video_version
from .views import get_categories, add_category
from .views import edit_category, delete_category
from .views import update_video_owner, filter_owners, filter_videos
from .views import PodChunkedUploadView, PodChunkedUploadCompleteView
from .views import stats_view
from .views import video_oembed

from .views import get_comments, get_children_comment
from .views import add_comment, delete_comment
from .views import vote_get, vote_post

app_name = "video"

urlpatterns = [
    # Manage video owner
    url(
        r"^updateowner/put/(?P<user_id>[\d]+)/$",
        update_video_owner,
        name="update_video_owner",
    ),
    url(r"^updateowner/owners/$", filter_owners, name="filter_owners"),
    url(
        r"^updateowner/videos/(?P<user_id>[\d]+)/$",
        filter_videos,
        name="filter_videos",
    ),
    url(r"^add/$", video_add, name="video_add"),
    url(r"^edit/$", video_edit, name="video_edit"),
    url(r"^edit/(?P<slug>[\-\d\w]+)/$", video_edit, name="video_edit"),
    url(
        r"^delete/(?P<slug>[\-\d\w]+)/$",
        video_delete,
        name="video_delete",
    ),
    url(r"^notes/(?P<slug>[\-\d\w]+)/$", video_notes, name="video_notes"),
    url(r"^count/(?P<id>[\d]+)/$", video_count, name="video_count"),
    url(r"^version/(?P<id>[\d]+)/$", video_version, name="video_version"),
    url(r"^xhr/(?P<slug>[\-\d\w]+)/$", video_xhr, name="video_xhr"),
    url(
        r"^xhr/(?P<slug>[\-\d\w]+)/(?P<slug_private>[\-\d\w]+)/$",
        video_xhr,
        name="video_xhr",
    ),
    url(
        "api/chunked_upload_complete/",
        PodChunkedUploadCompleteView.as_view(),
        name="api_chunked_upload_complete",
    ),
    url(
        "api/chunked_upload/",
        PodChunkedUploadView.as_view(),
        name="api_chunked_upload",
    ),
    url(r"^my/$", my_videos, name="my_videos"),
]
# COMPLETION
urlpatterns += [
    path("completion/", include("pod.completion.urls", namespace="completion")),
]
# CHAPTER
urlpatterns += [
    path("chapter/", include("pod.chapter.urls", namespace="chapter")),
]

##
# OEMBED feature patterns
#
if getattr(settings, "OEMBED", False):
    urlpatterns += [
        url(r"^oembed/", video_oembed, name="video_oembed"),
    ]

# VIDEO CATEGORY
if getattr(settings, "USER_VIDEO_CATEGORY", False):
    urlpatterns += [
        url(r"^my/categories/add/$", add_category, name="add_category"),
        url(
            r"^my/categories/edit/(?P<c_slug>[\-\d\w]+)/$",
            edit_category,
            name="edit_category",
        ),
        url(
            r"^my/categories/delete/(?P<c_id>[\d]+)/$",
            delete_category,
            name="delete_category",
        ),
        url(
            r"^my/categories/(?P<c_slug>[\-\d\w]+)/$",
            get_categories,
            name="get_category",
        ),
        url(r"^my/categories/$", get_categories, name="get_categories"),
    ]

if getattr(settings, "USE_STATS_VIEW", False):
    urlpatterns += [
        url(r"^stats_view/$", stats_view, name="video_stats_view"),
        url(
            r"^stats_view/(?P<slug>[-\w]+)/$",
            stats_view,
            name="video_stats_view",
        ),
        url(
            r"^stats_view/(?P<slug>[-\w]+)/(?P<slug_t>[-\w]+)/$",
            stats_view,
            name="video_stats_view",
        ),
    ]

# COMMENT and VOTE
if getattr(settings, "ACTIVE_VIDEO_COMMENT", False):
    urlpatterns += [
        url(
            r"^comment/(?P<video_slug>[\-\d\w]+)/$",
            get_comments,
            name="get_comments",
        ),
        url(
            r"^comment/(?P<comment_id>[\d]+)/(?P<video_slug>[\-\d\w]+)/$",
            get_children_comment,
            name="get_comment",
        ),
        url(
            r"^comment/add/(?P<video_slug>[\-\d\w]+)/$",
            add_comment,
            name="add_comment",
        ),
        url(
            r"^comment/add/(?P<video_slug>[\-\d\w]+)/(?P<comment_id>[\d]+)/$",
            add_comment,
            name="add_child_comment",
        ),
        url(
            r"^comment/del/(?P<video_slug>[\-\d\w]+)/(?P<comment_id>[\d]+)/$",
            delete_comment,
            name="delete_comment",
        ),
        url(
            r"^comment/vote/(?P<video_slug>[\-\d\w]+)/$",
            vote_get,
            name="get_votes",
        ),
        url(
            r"^comment/vote/(?P<video_slug>[\-\d\w]+)/(?P<comment_id>[\d]+)/$",
            vote_post,
            name="add_vote",
        ),
    ]

# DIRECT ACCESS TO A VIDEO
urlpatterns += [
    url(r"^(?P<slug>[\-\d\w]+)/$", video, name="video"),
    url(
        r"^(?P<slug>[\-\d\w]+)/(?P<slug_private>[\-\d\w]+)/$",
        video,
        name="video_private",
    ),
]
