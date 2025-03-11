from .rest_views import EnrichmentViewSet


def add_register(router):
    router.register(r"enrichments", EnrichmentViewSet)
