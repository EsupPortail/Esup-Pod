"""Tests for the video REST API."""

from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token

from ..models import Type, Video


class VideoRestApiTestCase(TestCase):
    """Check the serialized representation returned by the video API."""

    fixtures = ["initial_data.json"]

    def test_list_serializes_tagulous_tags_as_names(self) -> None:
        """A tagged video must not require a REST route for the tag model."""
        user = User.objects.create_superuser(
            username="rest-admin",
            email="rest-admin@example.com",
            password="test-password",
        )
        video = Video.objects.create(
            title="Tagged video",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(pk=1),
            tags="first-tag second-tag",
        )
        token = Token.objects.create(user=user)

        response = self.client.get(
            "/rest/videos/", HTTP_AUTHORIZATION=f"Token {token.key}"
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        result = response.json()["results"][0]
        self.assertEqual(result["id"], video.pk)
        self.assertCountEqual(result["tags"], ["first-tag", "second-tag"])
