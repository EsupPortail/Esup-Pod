from rest_framework import routers
from pod.authentication import rest_views as authentication_views

router = routers.DefaultRouter()
router.register(r'users', authentication_views.UserViewSet)
router.register(r'groups', authentication_views.GroupViewSet)