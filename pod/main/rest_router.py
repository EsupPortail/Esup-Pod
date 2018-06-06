from rest_framework import routers
from pod.authentication import rest_views as authentication_views
from pod.video import rest_views as video_views
from pod.filepicker import rest_views as filepicker_views


router = routers.DefaultRouter()
router.register(r'users', authentication_views.UserViewSet)
router.register(r'groups', authentication_views.GroupViewSet)
router.register(r'channels', video_views.ChannelViewSet)
router.register(r'themes', video_views.ThemeViewSet)
router.register(r'themes', video_views.ThemeViewSet)
router.register(r'themes', video_views.ThemeViewSet)
router.register(r'directories', filepicker_views.UserDirectorySerializerViewSet)
router.register(r'files', filepicker_views.CustomFileModelSerializerViewSet)
router.register(r'images', filepicker_views.CustomImageModelSerializerViewSet)