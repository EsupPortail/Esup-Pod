from django.urls import path
from .views import (
    add_recording,
    recorder_notify,
    claim_record,
    delete_record,
)

app_name = "record"

urlpatterns = [
    path("add_recording/", add_recording, name="add_recording"),
    path("recorder_notify/", recorder_notify, name="recorder_notify"),
    path("claim_record/", claim_record, name="claim_record"),
    path("delete_record/<int:id>/", delete_record, name="delete_record"),
]
