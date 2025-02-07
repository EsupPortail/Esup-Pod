"""Opencast Studio urls for Esup-Pod Integration."""

from django.urls import path, re_path
from .views import studio_pod, studio_static, studio_root_file
from .views import ingest_createMediaPackage, ingest_addDCCatalog
from .views import ingest_addAttachment, ingest_addTrack
from .views import ingest_addCatalog, ingest_ingest
from .views import presenter_post, settings_toml, info_me_json

app_name = "recorder"
urlpatterns = [
    path(
        "",
        studio_pod,
        name="studio_pod",
    ),
    path(
        "presenter_post",
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
    path(
        "ingest/createMediaPackage",
        ingest_createMediaPackage,
        name="ingest_createMediaPackage",
    ),
    path(
        "ingest/addDCCatalog",
        ingest_addDCCatalog,
        name="ingest_addDCCatalog",
    ),
    path(
        "ingest/addAttachment",
        ingest_addAttachment,
        name="ingest_addAttachment",
    ),
    path(
        "ingest/addTrack",
        ingest_addTrack,
        name="ingest_addTrack",
    ),
    path(
        "ingest/addCatalog",
        ingest_addCatalog,
        name="ingest_addCatalog",
    ),
    path(
        "ingest/ingest",
        ingest_ingest,
        name="ingest_ingest",
    ),
]
