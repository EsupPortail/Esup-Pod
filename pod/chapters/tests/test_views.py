"""
Unit tests for chapters views
"""
import os

from django.apps import apps
from django.conf import settings
from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from pod.video.models import Video
from pod.chapters.models import Chapter
if apps.is_installed('pod.filepicker'):
    from pod.filepicker.models import CustomFileModel
    from pod.filepicker.models import UserDirectory
    from datetime import datetime
    FILEPICKER = True
if apps.is_installed('pod.authentication'):
    from pod.authentication.models import Owner
    AUTH = True


class ChapterViewsTestCase(TestCase):

    def setUp(self):
        owner = User.objects.create(username='test', password='azerty')
        owner.set_password('hello')
        owner.save()
        Video.objects.create(
            title='videotest',
            owner=owner,
            video='test.mp4',
            duration=20
        )

    def test_video_chapter(self):
        video = Video.objects.get(id=1)
        response = self.client.get('/video_chapter/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 403)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/video_chapter/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_chapter.html')
        self.assertContains(response, 'videotest')
        self.assertContains(response, 'list_chapter')

        print(" [ BEGIN CHAPTER VIEWS ] ")
        print(" ---> test_video_chapter : OK!")

    def test_video_chapter_new(self):
        video = Video.objects.get(id=1)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_chapter/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_chapter.html')
        self.assertContains(response, 'videotest')
        self.assertContains(response, 'list_chapter')
        self.assertContains(response, 'form_chapter')
        response = self.client.post(
            '/video_chapter/{0}/'.format(video.slug),
            data={'action': 'save',
                  'chapter_id': None,
                  'video': 1,
                  'title': 'testchapter',
                  'time_start': 1,
                  'time_end': 3})
        self.assertEqual(response.status_code, 200)
        result = Chapter.objects.all()
        self.assertTrue(result)
        self.assertTemplateUsed('video_chapter.html')
        self.assertContains(response, 'videotest')
        self.assertContains(response, 'list_chapter')
        self.assertContains(response, 'testchapter')

        print(" ---> test_video_chapter_new : OK!")
        print(" [ END CHAPTER VIEWS ] ")

    def test_video_chapter_edit(self):
        video = Video.objects.get(id=1)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_chapter/{0}/'.format(video.slug),
            data={'action': 'save',
                  'chapter_id': None,
                  'video': 1,
                  'title': 'testchapter',
                  'time_start': 1,
                  'time_end': 3})
        self.assertEqual(response.status_code, 200)
        result = Chapter.objects.all()
        self.assertTrue(result)
        result = Chapter.objects.get(id=1)
        response = self.client.post(
            '/video_chapter/{0}/'.format(video.slug),
            data={'action': 'save',
                  'chapter_id': result.id,
                  'video': 1,
                  'title': 'testchapter2',
                  'time_start': 1,
                  'time_end': 4})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('video_chapter.html')
        self.assertContains(response, 'videotest')
        self.assertContains(response, 'list_chapter')
        self.assertContains(response, 'testchapter2')

        print(" ---> test_video_chapter_edit : OK!")

    def test_video_chapter_delete(self):
        video = Video.objects.get(id=1)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_chapter/{0}/'.format(video.slug),
            data={'action': 'save',
                  'chapter_id': None,
                  'video': 1,
                  'title': 'testchapter',
                  'time_start': 1,
                  'time_end': 3})
        self.assertEqual(response.status_code, 200)
        result = Chapter.objects.all()
        self.assertTrue(result)
        result = Chapter.objects.get(id=1)
        response = self.client.post(
            '/video_chapter/{0}/'.format(video.slug),
            data={'action': 'delete',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        result = Chapter.objects.all()
        self.assertFalse(result)

        print(" ---> test_video_chapter_delete : OK!")

    def test_video_chapter_import(self):
        video = Video.objects.get(id=1)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        file = SimpleUploadedFile(
            name='testfile.vtt',
            content=open(
                './pod/chapters/tests/testfile.vtt', 'rb').read(),
            content_type='text/plain')
        if FILEPICKER:
            home = UserDirectory.objects.get(id=1)
            user = User.objects.get(id=1)
            file = CustomFileModel.objects.create(
                name='testfile',
                date_created=datetime.now(),
                date_modified=datetime.now(),
                created_by=user,
                modified_by=user,
                directory=home,
                file=file
            ).id
        response = self.client.post(
            '/video_chapter/{0}/'.format(video.slug),
            data={'action': 'import',
                  'file': file})
        self.assertEqual(response.status_code, 200)
        result = Chapter.objects.all()
        self.assertTrue(result)
        result = Chapter.objects.get(id=1)
        self.assertEqual(result.title, 'Testchapter')

        print(" ---> test_video_chapter_import : OK!")
