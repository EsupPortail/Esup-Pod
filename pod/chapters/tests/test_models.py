"""
Unit tests for chapters models
"""
from django.apps import apps
from django.test import TestCase
from django.contrib.auth.models import User
from pod.video.models import Video
from pod.chapters.models import Chapter


class ChapterModelTestCase(TestCase):

    def setUp(self):
        owner = User.objects.create(username='test')
        video = Video.objects.create(
            title='video',
            owner=owner,
            video='test.mp4',
            duration=20
        )
        Chapter.objects.create(
            video=video,
            title='Chaptertest',
            time_start=1,
            time_end=2
        )
        Chapter.objects.create(
            video=video,
            title='Chaptertest2'
        )

    def test_attributs_full(self):
        chapter = Chapter.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(chapter.video, video)
        self.assertEqual(chapter.title, 'Chaptertest')
        self.assertEqual(chapter.slug, '{0}-{1}'.format('1', 'chaptertest'))
        self.assertEqual(chapter.time_start, 1)
        self.assertEqual(chapter.time_end, 2)

        print(" ---> test_attributs_full : OK ! --- ChapterModel")
        print(" [ END CHAPTER_TEST MODEL ] ")

    def test_attributs(self):
        chapter = Chapter.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(chapter.video, video)
        self.assertEqual(chapter.title, 'Chaptertest2')
        self.assertEqual(chapter.slug, '{0}-{1}'.format('2', 'chaptertest2'))
        self.assertEqual(chapter.time_start, 0)
        self.assertEqual(chapter.time_end, 1)

        print(" [ BEGIN CHAPTER_TEST MODEL ] ")
        print(" ---> test_attributs : OK ! --- ChapterModel")
