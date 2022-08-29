from django.conf.urls import url
from .views import studio_pod, studio_static, settings_toml, info_me_json
from .views import ingest_createMediaPackage, ingest_addDCCatalog
from .views import ingest_addAttachment, ingest_addTrack
from .views import ingest_addCatalog, ingest_ingest
from .views import presenter_post

from .rest_views import studio_services_available, studio_series, hello_world

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
# https://docs.opencast.org/r/11.x/developer/#modules/capture-agent/capture-agent/
# curl --digest -u pod:f446dd85ac968181ec1b023973cf2b1801dd03a9 -H "X-Requested-Auth: Digest" localhost:8080/rest/studio/services/available.json
url_rest_patterns = [
    # ${HOST}/services/available.json?serviceType=<SERVICE>
    url(r"^hello_world",
        hello_world
    ),
    url(
        r"^services/available.json$",
        studio_services_available,
        name="studio_services_available",
    ),
    # ${CAPTURE-ADMIN-ENDPOINT}/agents/<name>
    url(
        r"^admin-ng/series/(?P<file>.*)$",
        studio_series,
        name="studio_series",
    ),
    # /capture-admin/agents/$AGENT_NAME/configuration
    # ${CAPTURE-ADMIN-ENDPOINT}/agents/<name>
    url(
        r"^capture-admin/agents/agent_name/configuration$",
        studio_services_available,
        name="studio_services_available",
    ),
]