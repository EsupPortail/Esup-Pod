from rest_framework import routers
from django.apps import apps
from pod.authentication import rest_views as authentication_views
from pod.video import rest_views as video_views
if apps.is_installed('pod.chapters'):
    from pod.chapters import rest_views as chapter_views
if apps.is_installed('pod.filepicker'):
    from pod.filepicker import rest_views as filepicker_views
if apps.is_installed('pod.completion'):
    from pod.completion import rest_views as completion_views
if apps.is_installed('pod.enrichment'):
    from pod.enrichment import rest_views as enrichment_views


router = routers.DefaultRouter()
router.register(r'users', authentication_views.UserViewSet)
router.register(r'groups', authentication_views.GroupViewSet)
router.register(r'owners', authentication_views.OwnerViewSet)
router.register(r'images_owner',
                authentication_views.AuthenticationImageModelViewSet)

router.register(r'images_video', video_views.VideoImageModelViewSet)
router.register(r'channels', video_views.ChannelViewSet)
router.register(r'themes', video_views.ThemeViewSet)
router.register(r'types', video_views.TypeViewSet)
router.register(r'discipline', video_views.DisciplineViewSet)
router.register(r'videos', video_views.VideoViewSet)
router.register(r'renditions', video_views.VideoRenditionViewSet)
router.register(r'encodings_video', video_views.EncodingVideoViewSet)
router.register(r'encodings_audio', video_views.EncodingAudioViewSet)
router.register(r'playlist_videos', video_views.PlaylistVideoViewSet)

if apps.is_installed('pod.completion'):
    router.register(r'contributors', completion_views.ContributorViewSet)
    router.register(r'documents', completion_views.DocumentViewSet)
    router.register(r'tracks', completion_views.TrackViewSet)
    router.register(r'overlays', completion_views.OverlayViewSet)

if apps.is_installed('pod.enrichment'):
    router.register(r'enrichments', enrichment_views.EnrichmentViewSet)
    router.register(r'enrichments-file',
                    enrichment_views.EnrichmentFileViewSet)
    router.register(r'enrichments-image',
                    enrichment_views.EnrichmentImageViewSet)


if apps.is_installed('pod.chapters'):
    router.register(r'chapters', chapter_views.ChapterViewSet)

if apps.is_installed('pod.filepicker'):
    router.register(r'directories',
                    filepicker_views.UserDirectorySerializerViewSet)
    router.register(r'files',
                    filepicker_views.CustomFileModelSerializerViewSet)
    router.register(r'images',
                    filepicker_views.CustomImageModelSerializerViewSet)
