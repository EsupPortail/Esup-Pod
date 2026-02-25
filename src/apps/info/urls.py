from django.urls import path

from .views import ConfigInfoView, SystemInfoView

urlpatterns = [
    path("", SystemInfoView.as_view(), name="system_info"),
    path("conf", ConfigInfoView.as_view(), name="config_info"),
]
