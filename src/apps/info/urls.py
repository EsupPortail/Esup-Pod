from django.urls import path
from .views import SystemInfoView

urlpatterns = [
    path("", SystemInfoView.as_view(), name="system_info"),
]
