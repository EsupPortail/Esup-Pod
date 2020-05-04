"""
Unit tests for chapters views
"""
from django.conf import settings
from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from pod.video.models import Video, Type
from ..models import Chapter
from django.contrib.sites.models import Site

if getattr(settings, 'USE_PODFILE', False):
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder
    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel


class ChapterViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        site = Site.objects.get(id=1)
        owner = User.objects.create(
            username='test', password='azerty', is_staff=True)
        owner.set_password('hello')
        owner.save()
        owner2 = User.objects.create(username='test2', password='azerty')
        owner2.set_password('hello')
        owner2.save()
        vid = Video.objects.create(
            title='videotest',
            owner=owner,
            video='test.mp4',
            duration=20,
            type=Type.objects.get(id=1)
        )

        owner.owner.sites.add(Site.objects.get_current())
        owner.owner.save()

        owner2.owner.sites.add(Site.objects.get_current())
        owner2.owner.save()

        vid.sites.add(site)

    def test_video_chapter_owner(self):
        video = Video.objects.get(id=1)
        response = self.client.get('/video_chapter/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 302)

        self.user = User.objects.get(username="test")
        self.client.force_login(self.user)
        response = self.client.get('/video_chapter/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 200)

        authenticate(username='test2', password='hello')
        login = self.client.login(username='test2', password='hello')
        self.assertTrue(login)
        response = self.client.get('/video_chapter/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 403)  # forbidden

        print(" ---> test_video_chapter_owner : OK!")
        print(" [ END CHAPTER VIEWS ] ")

    def test_video_chapter(self):
        video = Video.objects.get(id=1)
        response = self.client.get('/video_chapter/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 302)
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
        fileChapter = SimpleUploadedFile(
            name='testfile.vtt',
            content=open(
                './pod/chapter/tests/testfile.vtt', 'rb').read(),
            content_type='text/plain')
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            user = User.objects.get(id=1)
            filevttchapter = CustomFileModel.objects.create(
                name='testfile',
                created_by=user,
                folder=home,
                file=fileChapter
            )
        else:
            filevttchapter = CustomFileModel.objects.create(
                file=fileChapter
            )
        response = self.client.post(
            '/video_chapter/{0}/'.format(video.slug),
            data={'action': 'import',
                  'file': filevttchapter.id})
        self.assertEqual(response.status_code, 200)
        result = Chapter.objects.all()
        self.assertTrue(result)
        result = Chapter.objects.get(id=1)
        self.assertEqual(result.title, 'Testchapter')

        print(" ---> test_video_chapter_import : OK!")
