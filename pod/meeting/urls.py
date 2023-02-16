from django.urls import path

from . import views

app_name = "meeting"

urlpatterns = [
    path("", views.my_meetings, name="my_meetings"),
    path("add/", views.add_or_edit, name="add"),
    path("edit/<slug:meeting_id>/", views.add_or_edit, name="edit"),
    path("delete/<slug:meeting_id>/", views.delete, name="delete"),
    path("status/<slug:meeting_id>/", views.status, name="status"),
    path("invite/<slug:meeting_id>/", views.invite, name="invite"),
    path(
        "get_meeting_info/<slug:meeting_id>/",
        views.get_meeting_info,
        name="get_meeting_info",
    ),
    path("end/<slug:meeting_id>/", views.end, name="end"),
    path("end_callback/<slug:meeting_id>/", views.end_callback, name="end_callback"),
    path("<slug:meeting_id>/", views.join, name="join"),
    path("<slug:meeting_id>/<slug:direct_access>", views.join, name="join"),
]
