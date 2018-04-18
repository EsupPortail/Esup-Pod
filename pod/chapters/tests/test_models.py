"""
Unit tests for chapters models
"""
from django.apps import apps
from django.test import TestCase
from pod.video.models import Video
from pod.chapters.models import Chapter
if apps.is_installed('pod.authentication'):
    AUTH = True
    from django.contrib.auth.models import User
    from pod.authentication.models import Owner
else:
    AUTH = False
    from django.contrib.auth.models import User


class ChapterModelTestCase(TestCase):

    def setUp(self):
        User.objects.create(username='test')
        owner = Owner.objects.get(user__username='test')
        video = Video.objects.create(
            title='video',
            owner=owner,
            video='test.mp4',
            duration=20
        )
        Chapter.objects.create(
            video=video,
            title='Chaptertest',
            time=1
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
        self.assertEqual(chapter.slug, 'chaptertest')
        self.assertEqual(chapter.time, 1)

        print(" ---> test_attributs_full : OK ! --- ChapterModel")

    def test_attributs(self):
        chapter = Chapter.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(chapter.video, video)
        self.assertEqual(chapter.title, 'Chaptertest2')
        self.assertEqual(chapter.slug, 'chaptertest2')
        self.assertEqual(chapter.time, 0)

        print(" ---> test_attributs : OK ! --- ChapterModel")
