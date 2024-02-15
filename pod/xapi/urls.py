"""Esup-Pod xAPI urls."""

from django.urls import path

from . import views

app_name = "xapi"

urlpatterns = [
    path("", views.statement, name="statement"),
    path("<slug:app>/", views.statement, name="statement"),
]
