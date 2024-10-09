"""create_pod_index management command."""

from django.core.management.base import BaseCommand
from pod.video_search.utils import create_index_es, delete_index_es
from elasticsearch import exceptions
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command called by `python manage.py create_pod_index`."""

    args = ""
    help = "Creates the Elasticsearch Pod index."

    def handle(self, *args, **options):
        """Create the Elasticsearch Pod index."""
        try:
            delete_index_es()
            self.stdout.write(self.style.WARNING("The Pod index has been deleted."))
        except exceptions.NotFoundError:
            self.stdout.write(
                self.style.WARNING("Pod index not found on ElasticSearch server.")
            )
        create_index_es()
        self.stdout.write(self.style.SUCCESS("Video index successfully created on ES."))
