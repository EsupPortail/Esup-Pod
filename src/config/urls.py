from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  

from config.router import router

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Redirection to Swagger
    path("", RedirectView.as_view(url="api/docs/", permanent=False)), 

    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/info/", include('src.apps.info.urls')),
    path('api/auth/', include('src.apps.authentication.urls')),

    # SWAGGER 
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]