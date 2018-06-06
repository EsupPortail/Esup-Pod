from rest_framework import routers
from django.apps import apps
from pod.authentication import rest_views as authentication_views
from pod.video import rest_views as video_views
if apps.is_installed('pod.filepicker'):
    from pod.filepicker import rest_views as filepicker_views


router = routers.DefaultRouter()
router.register(r'users', authentication_views.UserViewSet)
router.register(r'groups', authentication_views.GroupViewSet)

router.register(r'channels', video_views.ChannelViewSet)
router.register(r'themes', video_views.ThemeViewSet)
router.register(r'types', video_views.TypeViewSet)
router.register(r'discipline', video_views.DisciplineViewSet)
router.register(r'videos', video_views.VideoViewSet)
router.register(r'renditions', video_views.VideoRenditionViewSet)
router.register(r'encodings_video', video_views.EncodingVideoViewSet)
router.register(r'encodings_audio', video_views.EncodingAudioViewSet)
router.register(r'playlist_videos', video_views.PlaylistVideoViewSet)

if apps.is_installed('pod.filepicker'):
    router.register(r'directories', filepicker_views.UserDirectorySerializerViewSet)
    router.register(r'files', filepicker_views.CustomFileModelSerializerViewSet)
    router.register(r'images', filepicker_views.CustomImageModelSerializerViewSet)