"""Opencast Studio urls for Esup-Pod Integration."""
from django.conf.urls import url
from .views import studio_pod, studio_static, studio_root_file
from .views import ingest_createMediaPackage, ingest_addDCCatalog
from .views import ingest_addAttachment, ingest_addTrack
from .views import ingest_addCatalog, ingest_ingest
from .views import presenter_post, settings_toml, info_me_json

app_name = "recorder"
urlpatterns = [
    url(
        r"^$",
        studio_pod,
        name="studio_pod",
    ),
    url(
        r"^presenter_post$",
        presenter_post,
        name="presenter_post",
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
        r"^(?P<file>[a-zA-Z0-9\.]*)$",
        studio_root_file,
        name="studio_root_file",
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
    url(
        r"^ingest/addAttachment$",
        ingest_addAttachment,
        name="ingest_addAttachment",
    ),
    url(
        r"^ingest/addTrack$",
        ingest_addTrack,
        name="ingest_addTrack",
    ),
    url(
        r"^ingest/addCatalog$",
        ingest_addCatalog,
        name="ingest_addCatalog",
    ),
    url(
        r"^ingest/ingest$",
        ingest_ingest,
        name="ingest_ingest",
    ),
]
