"""Esup-Pod Main REST api url router."""
from rest_framework import routers
from django.conf.urls import url
from django.conf.urls import include
from pod.authentication import rest_views as authentication_views
from pod.video import rest_views as video_views
from pod.main import rest_views as main_views
from pod.authentication import rest_views as auth_views
from pod.video_encode_transcript import rest_views as encode_views

from pod.chapter import rest_views as chapter_views
from pod.completion import rest_views as completion_views
from pod.playlist import rest_views as playlist_views
from pod.recorder import rest_views as recorder_views

from django.conf import settings

import importlib

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile import rest_views as podfile_views

if getattr(settings, "USE_BBB", True):
    from pod.bbb import rest_views as bbb_views

router = routers.DefaultRouter()

router.register(r"mainfiles", main_views.CustomFileModelViewSet)
router.register(r"mainimages", main_views.CustomImageModelViewSet)

router.register(r"users", authentication_views.UserViewSet)
router.register(r"groups", authentication_views.GroupViewSet)
router.register(r"owners", authentication_views.OwnerViewSet)
router.register(r"sites", authentication_views.SiteViewSet)
router.register(r"accessgroups", authentication_views.AccessGroupViewSet)

router.register(r"channels", video_views.ChannelViewSet)
router.register(r"themes", video_views.ThemeViewSet)
router.register(r"types", video_views.TypeViewSet)
router.register(r"discipline", video_views.DisciplineViewSet)
router.register(r"videos", video_views.VideoViewSet)
router.register(r"renditions", encode_views.VideoRenditionViewSet)
router.register(r"encodings_video", encode_views.EncodingVideoViewSet)
router.register(r"encodings_audio", encode_views.EncodingAudioViewSet)
router.register(r"playlist_videos", encode_views.PlaylistVideoViewSet)
router.register(r"view_count", video_views.ViewCountViewSet)

router.register(r"playlists", playlist_views.PlaylistViewSet)

router.register(r"contributors", completion_views.ContributorViewSet)
router.register(r"documents", completion_views.DocumentViewSet)
router.register(r"tracks", completion_views.TrackViewSet)
router.register(r"overlays", completion_views.OverlayViewSet)

router.register(r"chapters", chapter_views.ChapterViewSet)

router.register(r"recording", recorder_views.RecordingModelViewSet)
router.register(r"recordingfile", recorder_views.RecordingFileModelViewSet)
router.register(
    r"recordingfiletreatment", recorder_views.RecordingFileTreatmentModelViewSet
)
router.register(r"recorder", recorder_views.RecorderModelViewSet)

if getattr(settings, "USE_PODFILE", False):
    router.register(r"folders", podfile_views.UserFolderSerializerViewSet)
    router.register(r"files", podfile_views.CustomFileModelSerializerViewSet)
    router.register(r"images", podfile_views.CustomImageModelSerializerViewSet)

if getattr(settings, "USE_BBB", True):
    router.register(r"bbb_meeting", bbb_views.MeetingModelViewSet)
    router.register(r"bbb_attendee", bbb_views.AttendeeModelViewSet)
    router.register(r"bbb_livestream", bbb_views.LivestreamModelViewSet)

urlpatterns = [
    url(r"dublincore/$", video_views.DublinCoreView.as_view(), name="dublincore"),
    url(
        r"launch_encode_view/$",
        encode_views.launch_encode_view,
        name="launch_encode_view",
    ),
    url(
        r"store_remote_encoded_video/$",
        encode_views.store_remote_encoded_video,
        name="store_remote_encoded_video",
    ),
    url(
        r"accessgroups_set_users_by_name/$",
        auth_views.accessgroups_set_users_by_name,
        name="accessgroups_set_users_by_name",
    ),
    url(
        r"accessgroups_remove_users_by_name/$",
        auth_views.accessgroups_remove_users_by_name,
        name="accessgroups_set_users_by_name",
    ),
    url(
        r"accessgroups_set_user_accessgroup /$",
        auth_views.accessgroups_set_user_accessgroup,
        name="accessgroups_set_user_accessgroup ",
    ),
    url(
        r"accessgroups_remove_user_accessgroup /$",
        auth_views.accessgroups_remove_user_accessgroup,
        name="accessgroups_remove_user_accessgroup ",
    ),
]
USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)
if USE_TRANSCRIPTION:
    urlpatterns += [
        url(
            r"launch_transcript_view/$",
            encode_views.launch_transcript_view,
            name="launch_transcript_view",
        ),
    ]

for apps in settings.THIRD_PARTY_APPS:
    mod = importlib.import_module("pod.%s.rest_urls" % apps)
    mod.add_register(router)

urlpatterns += [
    url(r"^", include(router.urls)),
]
