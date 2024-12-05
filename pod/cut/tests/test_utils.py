"""Unit tests for video cut utils."""

import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from pod.cut.utils import clean_database
from pod.video.models import Notes, AdvancedNotes, Type, Video
from pod.chapter.models import Chapter
from pod.completion.models import Overlay, Track

USE_CUT = getattr(settings, "USE_CUT", False)


@unittest.skipUnless(USE_CUT, "Set USE_CUT to True before testing video cut stuffs.")
class CleanDatabaseTest(TestCase):
    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        self.user = User.objects.create(username="pod", password="pod1234pod")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.chapter = Chapter.objects.create(video=self.video, title="Chapter 1")
        self.advanced_notes = AdvancedNotes.objects.create(
            video=self.video, user=self.user, note="Advanced note content"
        )
        self.notes = Notes.objects.create(
            video=self.video, user=self.user, note="Note content"
        )
        self.overlay = Overlay.objects.create(video=self.video, title="Overlay 1")
        self.track = Track.objects.create(video=self.video)

    def test_clean_database(self) -> None:
        """Test if clean_database works correctly."""
        # Check if the models exist before cleaning
        self.assertTrue(Chapter.objects.filter(video=self.video).exists())
        self.assertTrue(AdvancedNotes.objects.filter(video=self.video).exists())
        self.assertTrue(Notes.objects.filter(video=self.video).exists())
        self.assertTrue(Overlay.objects.filter(video=self.video).exists())
        self.assertTrue(Track.objects.filter(video=self.video).exists())

        # Call clean_database
        clean_database(self.video)

        # Check if the models are deleted after cleaning
        self.assertFalse(Chapter.objects.filter(video=self.video).exists())
        self.assertFalse(AdvancedNotes.objects.filter(video=self.video).exists())
        self.assertFalse(Notes.objects.filter(video=self.video).exists())
        self.assertFalse(Overlay.objects.filter(video=self.video).exists())
        self.assertFalse(Track.objects.filter(video=self.video).exists())

        print(" --->  test_clean_database ok")
