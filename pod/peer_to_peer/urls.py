from django.urls import path

from .views import (
    get_csrf_token,
    get_ids_by_urls,
    store_urls_id,
    test,
    clear_invalid_peer_in_caches,
)

app_name = "peer_to_peer"

urlpatterns = [
    path("get-ids/", get_ids_by_urls, name="get-ids-by-urls"),
    path("store/<str:id>/", store_urls_id, name="store-urls-id"),
    path("get-csrf/", get_csrf_token, name="get-csrf"),
    path("test/", test, name="test"),
    path("clear-invalid-peer/", clear_invalid_peer_in_caches, name="clear-invalid-peer")
]
