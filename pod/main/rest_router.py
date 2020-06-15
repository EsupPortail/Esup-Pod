from rest_framework import routers
from django.conf.urls import url
from django.conf.urls import include
from pod.authentication import rest_views as authentication_views
from pod.video import rest_views as video_views
from pod.main import rest_views as main_views

from pod.chapter import rest_views as chapter_views
from pod.completion import rest_views as completion_views
from pod.recorder import rest_views as recorder_views

from django.conf import settings

import importlib

if getattr(settings, 'USE_PODFILE', False):
    from pod.podfile import rest_views as podfile_views

router = routers.DefaultRouter()

router.register(r'mainfiles', main_views.CustomFileModelViewSet)
router.register(r'mainimages', main_views.CustomImageModelViewSet)

router.register(r'users', authentication_views.UserViewSet)
router.register(r'groups', authentication_views.GroupViewSet)
router.register(r'owners', authentication_views.OwnerViewSet)

router.register(r'channels', video_views.ChannelViewSet)
router.register(r'themes', video_views.ThemeViewSet)
router.register(r'types', video_views.TypeViewSet)
router.register(r'discipline', video_views.DisciplineViewSet)
router.register(r'videos', video_views.VideoViewSet)
router.register(r'renditions', video_views.VideoRenditionViewSet)
router.register(r'encodings_video', video_views.EncodingVideoViewSet)
router.register(r'encodings_audio', video_views.EncodingAudioViewSet)
router.register(r'playlist_videos', video_views.PlaylistVideoViewSet)

router.register(r'contributors', completion_views.ContributorViewSet)
router.register(r'documents', completion_views.DocumentViewSet)
router.register(r'tracks', completion_views.TrackViewSet)
router.register(r'overlays', completion_views.OverlayViewSet)

router.register(r'chapters', chapter_views.ChapterViewSet)

router.register(r'recording', recorder_views.RecordingModelViewSet)
router.register(r'recordingfile', recorder_views.RecordingFileModelViewSet)
router.register(r'recorder', recorder_views.RecorderModelViewSet)

if getattr(settings, 'USE_PODFILE', False):
    router.register(r'folders',
                    podfile_views.UserFolderSerializerViewSet)
    router.register(r'files',
                    podfile_views.CustomFileModelSerializerViewSet)
    router.register(r'images',
                    podfile_views.CustomImageModelSerializerViewSet)

urlpatterns = [
    url(r'dublincore/$', video_views.DublinCoreView.as_view(),
        name='dublincore'),
    url(r'launch_encode_view/$', video_views.launch_encode_view,
        name='launch_encode_view'),
]

for apps in settings.THIRD_PARTY_APPS:
    mod = importlib.import_module('pod.%s.rest_urls' % apps)
    mod.add_register(router)

urlpatterns += [url(r'^', include(router.urls)), ]
