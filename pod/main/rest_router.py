from rest_framework import routers
from django.conf.urls import url
from django.conf.urls import include
from pod.authentication import rest_views as authentication_views
from pod.video import rest_views as video_views
from pod.main import rest_views as main_views

from pod.chapter import rest_views as chapter_views
from pod.completion import rest_views as completion_views
"""
from django.conf import settings
if getattr(settings, 'USE_PODFILE', False):
    from pod.podfile import rest_views as podfile_views

if 'enrichment' in settings.THIRD_PARTY_APPS:
    from pod.enrichment import rest_views as enrichment_views
"""

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
"""
if 'enrichment' in settings.THIRD_PARTY_APPS:
    router.register(r'enrichments', enrichment_views.EnrichmentViewSet)
    router.register(r'enrichments-file',
                    enrichment_views.EnrichmentFileViewSet)
    router.register(r'enrichments-image',
                    enrichment_views.EnrichmentImageViewSet)
"""
router.register(r'chapters', chapter_views.ChapterViewSet)
"""
if apps.is_installed('pod.filepicker'):
    router.register(r'directories',
                    filepicker_views.UserDirectorySerializerViewSet)
    router.register(r'files',
                    filepicker_views.CustomFileModelSerializerViewSet)
    router.register(r'images',
                    filepicker_views.CustomImageModelSerializerViewSet)
"""
urlpatterns = [
    url(r'dublincore/$', video_views.DublinCoreView.as_view(),
        name='dublincore'),
    url(r'^', include(router.urls)),
]
