from django.urls import path
from pod.dressing.views import video_dressing, my_dressings, dressing_edit
from pod.dressing.views import dressing_create, dressing_delete

app_name = "dressing"

urlpatterns = [
    path("my/", my_dressings, name="my_dressings"),
    path("edit/<slug:dressing_id>/", dressing_edit, name="dressing_edit"),
    path("new/", dressing_create, name="dressing_create"),
    path("delete/<slug:dressing_id>/", dressing_delete, name="dressing_delete"),
    path("<slug:slug>/", video_dressing, name="video_dressing"),
]
