from .rest_views import BuildingViewSet, BroadcasterViewSet, EventViewSet


def add_register(router):
    router.register(r"buildings", BuildingViewSet)
    router.register(r"broadcasters", BroadcasterViewSet)
    router.register(r"events", EventViewSet)
