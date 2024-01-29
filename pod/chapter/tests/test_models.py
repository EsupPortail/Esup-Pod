"""Unit tests for chapters models."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from pod.video.models import Video
from pod.video.models import Type
from ..models import Chapter


class ChapterModelTestCase(TestCase):
    """Test case for Pod chapter model."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        owner = User.objects.create(username="test")
        videotype = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video",
            type=videotype,
            owner=owner,
            video="test.mp4",
            duration=20,
        )
        Chapter.objects.create(video=video, title="Chaptertest", time_start=1)
        Chapter.objects.create(video=video, title="Chaptertest2")

    def test_attributs_full(self):
        chapter = Chapter.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(chapter.video, video)
        self.assertEqual(chapter.title, "Chaptertest")
        self.assertEqual(chapter.slug, "{0}-{1}".format(chapter.id, "chaptertest"))
        self.assertEqual(chapter.time_start, 1)

        print(" ---> test_attributs_full: OK! --- ChapterModel")

    def test_attributs(self):
        chapter = Chapter.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(chapter.video, video)
        self.assertEqual(chapter.title, "Chaptertest2")
        self.assertEqual(chapter.slug, "{0}-{1}".format(chapter.id, "chaptertest2"))
        self.assertEqual(chapter.time_start, 0)

        print(" [ BEGIN CHAPTER_TEST MODEL ] ")
        print(" ---> test_attributs: OK! --- ChapterModel")

    def test_without_title(self):
        video = Video.objects.get(id=1)
        chapter = Chapter()
        chapter.time_start = 1
        chapter.video = video
        self.assertRaises(ValidationError, chapter.clean)

        print(" ---> test_without_title: OK! --- ChapterModel")
        print(" [ END CHAPTER_TEST MODEL ] ")

    def test_bad_time(self):
        video = Video.objects.get(id=1)
        chapter = Chapter()
        chapter.video = video
        chapter.title = "test"
        self.assertRaises(ValidationError, chapter.clean)
        chapter.time_start = 21
        self.assertRaises(ValidationError, chapter.clean)
        chapter.time_start = -1
        self.assertRaises(ValidationError, chapter.clean)

        print(" ---> test_bad_time: OK! --- ChapterModel")

    def test_overlap(self):
        video = Video.objects.get(id=1)
        chapter = Chapter()
        chapter.video = video
        chapter.title = "test"
        chapter.time_start = 1
        self.assertRaises(ValidationError, chapter.clean)

        print(" ---> test_overlap: OK! --- ChapterModel")
