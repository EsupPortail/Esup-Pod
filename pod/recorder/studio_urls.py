from django.conf.urls import url
from .views import studio_pod, studio_static, settings_toml, info_me_json
from .views import ingest_createMediaPackage, ingest_addDCCatalog

app_name = "recorder"
urlpatterns = [
    url(
        r"^$",
        studio_pod,
        name="studio_pod",
    ),
    url(
        r"^settings.toml$",
        settings_toml,
        name="settings_toml",
    ),
    url(
        r"^info/me.json$",
        info_me_json,
        name="info_me_json",
    ),
    url(
        r"^static/(?P<file>.*)$",
        studio_static,
        name="studio_static",
    ),
    url(
        r"^ingest/createMediaPackage$",
        ingest_createMediaPackage,
        name="ingest_createMediaPackage",
    ),
    url(
        r"^ingest/addDCCatalog$",
        ingest_addDCCatalog,
        name="ingest_addDCCatalog",
    ),
]
