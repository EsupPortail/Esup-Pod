"""Opencast Studio urls for Esup-Pod Integration."""

from django.urls import re_path
from .views import studio_pod, studio_static, studio_root_file
from .views import ingest_createMediaPackage, ingest_addDCCatalog
from .views import ingest_addAttachment, ingest_addTrack
from .views import ingest_addCatalog, ingest_ingest
from .views import presenter_post, settings_toml, info_me_json

app_name = "recorder"
urlpatterns = [
    re_path(
        r"^$",
        studio_pod,
        name="studio_pod",
    ),
    re_path(
        r"^presenter_post$",
        presenter_post,
        name="presenter_post",
    ),
    re_path(
        r"^settings.toml$",
        settings_toml,
        name="settings_toml",
    ),
    re_path(
        r"^info/me.json$",
        info_me_json,
        name="info_me_json",
    ),
    re_path(
        r"^static/(?P<file>.*)$",
        studio_static,
        name="studio_static",
    ),
    re_path(
        r"^(?P<file>[a-zA-Z0-9\.]*)$",
        studio_root_file,
        name="studio_root_file",
    ),
    re_path(
        r"^ingest/createMediaPackage$",
        ingest_createMediaPackage,
        name="ingest_createMediaPackage",
    ),
    re_path(
        r"^ingest/addDCCatalog$",
        ingest_addDCCatalog,
        name="ingest_addDCCatalog",
    ),
    re_path(
        r"^ingest/addAttachment$",
        ingest_addAttachment,
        name="ingest_addAttachment",
    ),
    re_path(
        r"^ingest/addTrack$",
        ingest_addTrack,
        name="ingest_addTrack",
    ),
    re_path(
        r"^ingest/addCatalog$",
        ingest_addCatalog,
        name="ingest_addCatalog",
    ),
    re_path(
        r"^ingest/ingest$",
        ingest_ingest,
        name="ingest_ingest",
    ),
]
