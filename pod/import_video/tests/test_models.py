"""Tests the models for import_video module."""

from ..models import ExternalRecording
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase


class ExternalRecordingTestCase(TestCase):
    """List of recordings model tests, only external.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        """Set up for the recordings."""
        user = User.objects.create(username="pod")
        ExternalRecording.objects.create(
            id=1,
            name="test recording1",
            owner=user,
            start_at=datetime(2022, 4, 24, 14, 0, 0),
            site=Site.objects.get(id=1),
            type="bigbluebutton",
            source_url="https://bbb.url",
        )
        ExternalRecording.objects.create(
            id=2,
            name="test recording2",
            owner=user,
            start_at=datetime(2022, 4, 24, 14, 0, 0),
            site=Site.objects.get(id=1),
            type="bigbluebutton",
            source_url="https://bbb.url",
            uploaded_to_pod_by=user,
        )

    def test_default_attributs(self):
        """Check all default attributs values when creating a recording."""
        recordings = ExternalRecording.objects.all()
        self.assertGreaterEqual(
            recordings[0].start_at.date(), recordings[1].start_at.date()
        )

    def test_with_attributs(self):
        """Check all attributs values passed when creating a recording."""
        recording2 = ExternalRecording.objects.get(id=2)
        self.assertEqual(recording2.name, "test recording2")
        user = User.objects.get(username="pod")
        self.assertEqual(recording2.uploaded_to_pod_by, user)

    def test_change_attributs(self):
        """Change attributs values in a recording and save it."""
        recording1 = ExternalRecording.objects.get(id=1)
        self.assertEqual(recording1.name, "test recording1")
        recording1.name = "New test recording1!"
        recording1.save()
        newrecording1 = ExternalRecording.objects.get(id=1)
        self.assertEqual(newrecording1.name, "New test recording1!")

    def test_delete_object(self):
        """Delete a recording."""
        ExternalRecording.objects.filter(name="test recording2").delete()
        self.assertEqual(ExternalRecording.objects.all().count(), 1)
