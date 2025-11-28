from django.urls import path
from .views import SystemInfoView, SystemInfoView2

urlpatterns = [
    path('', SystemInfoView.as_view(), name='system_info'),
]