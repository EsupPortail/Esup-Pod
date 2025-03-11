"""URLS for Import_video module."""

from django.urls import path

from . import views

app_name = "import_video"

urlpatterns = [
    path("", views.external_recordings, name="external_recordings"),
    path(
        "add",
        views.add_or_edit_external_recording,
        name="add_external_recording",
    ),
    path(
        "edit/<slug:id>/",
        views.add_or_edit_external_recording,
        name="edit_external_recording",
    ),
    path(
        "<slug:record_id>/",
        views.upload_external_recording_to_pod,
        name="upload_external_recording_to_pod",
    ),
    path(
        "delete/<slug:id>/",
        views.delete_external_recording,
        name="delete_external_recording",
    ),
    path(
        "recording_with_token/<slug:id>/",
        views.recording_with_token,
        name="recording_with_token",
    ),
]
