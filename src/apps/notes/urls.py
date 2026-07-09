"""
Esup-Pod - Notes application URL configuration.
"""

from rest_framework.routers import SimpleRouter
from src.apps.notes.views import VideoNoteViewSet
from src.apps.notes.conf import notes_settings

router = SimpleRouter()

if notes_settings.use_notes:
    router.register(r"notes", VideoNoteViewSet, basename="note")

urlpatterns = router.urls
