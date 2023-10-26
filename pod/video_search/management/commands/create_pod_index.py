"""create_pod_index management command."""
from django.core.management.base import BaseCommand
from django.conf import settings
from pod.video_search.utils import create_index_es, delete_index_es

import logging

logger = logging.getLogger(__name__)

ES_URL = getattr(settings, "ES_URL", ["http://127.0.0.1:9200/"])


class Command(BaseCommand):
    """Command called by `python manage.py create_pod_index`."""

    args = ""
    help = "Creates the Elasticsearch Pod index."

    def handle(self, *args, **options):
        """Create the Elasticsearch Pod index."""
        delete_index_es()
        create_index_es()
        self.stdout.write(self.style.SUCCESS("Video index successfully created on ES."))
