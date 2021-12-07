from django.conf.urls import url
from .views import ingest_createMediaPackage, ingest_addDCCatalog


urlpatterns = [
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
