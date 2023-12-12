from django.urls import path

from .views import (
    get_csrf_token,
    get_ids_by_urls,
    store_urls_id,
    test,
)

app_name = "peer_to_peer"

urlpatterns = [
    path("get-ids/", get_ids_by_urls, name="get-ids-by-urls"),
    path("store/<int:id>/", store_urls_id, name="store-urls-id"),
    path("get-csrf/", get_csrf_token, name="get-csrf"),
    path("test/", test, name="test"),
]
