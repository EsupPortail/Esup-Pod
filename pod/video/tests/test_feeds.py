"""Unit test case for Pod video feeds."""

from django.test import TestCase
from django.test import Client
from http import HTTPStatus
from django.urls import reverse

from defusedxml import minidom


class FeedTestView(TestCase):
    """Test case for Pod video feeds view."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        pass

    def test_get_rss_video_from_video(self) -> None:
        self.client = Client()
        url = reverse("rss-video:rss-video", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mediaPackage_content = minidom.parseString(response.content)
        mediapackage = mediaPackage_content.getElementsByTagName("rss")[0]
        self.assertTrue(mediapackage)
        print(" -->  test_get_rss_video_from_video of FeedTestView", ": OK!")

    def test_get_rss_audio_from_video(self) -> None:
        self.client = Client()
        url = reverse("rss-video:rss-audio", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mediaPackage_content = minidom.parseString(response.content)
        mediapackage = mediaPackage_content.getElementsByTagName("rss")[0]
        self.assertTrue(mediapackage)
        print(" -->  test_get_rss_audio_from_video of FeedTestView", ": OK!")
