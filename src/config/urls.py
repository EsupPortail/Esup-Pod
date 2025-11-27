from django.contrib import admin
from django.urls import path, include
# Correction: import depuis 'router' (singulier) et non 'routers'
from config.router import router

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/auth/", include("rest_framework.urls")), # Login browsable API
]