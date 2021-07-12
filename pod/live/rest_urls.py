from .rest_views import BuildingViewSet, BroadcasterViewSet


def add_register(router):
    router.register(r"buildings", BuildingViewSet)
    router.register(r"broadcasters", BroadcasterViewSet)
