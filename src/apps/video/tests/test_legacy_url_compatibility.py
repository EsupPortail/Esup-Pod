"""
Esup-Pod - Tests for URLs legacy compatibility between V4 and V5.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from src.apps.video.models import Video

User = get_user_model()


class MigrationURLTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="migrationuser", password="password"
        )

    def test_legacy_url_compatibility(self):
        # 1. Créer une vidéo test
        video = Video.objects.create(
            title="Washington Landlord",
            id=46859,
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )

        # 2. Simuler l'URL Lille de permalien générée par Django
        expected_absolute_url = f"/video/{video.pk}-{video.slug}/"

        # 3. Vérifier que get_absolute_url() produit bien ce format compatible
        self.assertEqual(video.get_absolute_url(), expected_absolute_url)
        self.assertIn("46859", video.get_absolute_url())

        # 4. Vérifier que l'API de streaming de la V5 comprend ce format de slug
        legacy_api_url = f"/api/videos/{video.pk}-washingtonlandlordtenantlawmp4/"
        response = self.client.get(legacy_api_url)

        # Le ViewSet doit comprendre et rediriger/renvoyer 200 via l'API.
        self.assertEqual(response.status_code, 200)
