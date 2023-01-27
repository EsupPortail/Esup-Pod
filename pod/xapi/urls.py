from django.urls import path

from . import views

app_name = "xapi"

urlpatterns = [
    path("", views.statement, name="statement"),
]
