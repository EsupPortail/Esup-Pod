"""
Unit tests for completion views
"""
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from pod.video.models import Video, Type
from ..models import Contributor
from ..models import Document
from ..models import Overlay
from ..models import Track
from datetime import datetime
from django.contrib.sites.models import Site

if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel


class CompletionViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username='test', password='azerty')
        user.set_password('hello')
        user.save()
        staff = User.objects.create(
            username='staff', password='azerty', is_staff=True)
        staff.set_password('hello')
        staff.save()
        vid1 = Video.objects.create(
            title='videotest',
            owner=user,
            video='test.mp4',
            type=Type.objects.get(id=1)
        )
        vid1.sites.add(site)
        vid2 = Video.objects.create(
            title='videotest2',
            owner=staff,
            video='test.mp4',
            type=Type.objects.get(id=1)
        )
        vid2.sites.add(site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_user(self):
        video = Video.objects.get(id=1)
        response = self.client.get('/video_completion/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/video_completion/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'videotest')
        self.assertContains(response, 'list_contributor')

        print(" ---> test_video_completion_user : OK!")

    def test_video_completion_staff(self):
        video = Video.objects.get(id=2)
        response = self.client.get('/video_completion/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.get('/video_completion/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'videotest2')
        self.assertContains(response, 'list_contributor')
        self.assertContains(response, 'list_track')
        self.assertContains(response, 'list_document')
        self.assertContains(response, 'list_overlay')

        print(" ---> test_video_completion_staff : OK!")


class CompletionContributorViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        site = Site.objects.get(id=1)
        staff = User.objects.create(
            username='staff', password='azerty', is_staff=True)
        staff.set_password('hello')
        staff.save()
        vid = Video.objects.create(
            title='videotest2',
            owner=staff,
            video='test.mp4',
            type=Type.objects.get(id=1)
        )
        vid.sites.add(site)
        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_contributor(self):
        video = Video.objects.get(id=1)
        response = self.client.get(
            '/video_completion_contributor/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.get(
            '/video_completion_contributor/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'videotest2')
        self.assertContains(response, 'list_contributor')
        self.assertContains(response, 'list_track')
        self.assertContains(response, 'list_document')
        self.assertContains(response, 'list_overlay')

        print(" [ BEGIN COMPLETION_CONTRIBUTOR VIEWS ] ")
        print(" ---> test_video_completion_contributor : OK!")

    def test_video_completion_contributor_new(self):
        video = Video.objects.get(id=1)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_contributor/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_contributor')
        response = self.client.post(
            '/video_completion_contributor/{0}/'.format(video.slug),
            data={'action': 'save',
                  'name': 'testcontributor',
                  'role': 'author',
                  'video': 1,
                  'email_address': 'test@test.com',
                  'weblink': '',
                  'contributor_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'list_contributor')
        self.assertContains(response, 'testcontributor')
        self.assertContains(response, 'test@test.com')
        result = Contributor.objects.get(id=1)
        self.assertEqual(result.name, 'testcontributor')

        print(" ---> test_video_completion_contributor_new : OK!")
        print(" [ END COMPLETION_CONTRIBUTOR VIEWS ] ")

    def test_video_completion_contributor_edit(self):
        video = Video.objects.get(id=1)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_contributor/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_contributor')
        response = self.client.post(
            '/video_completion_contributor/{0}/'.format(video.slug),
            data={'action': 'save',
                  'name': 'testcontributor',
                  'role': 'author',
                  'video': 1,
                  'email_address': 'test@test.com',
                  'weblink': '',
                  'contributor_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_contributor')
        result = Contributor.objects.get(id=1)
        self.assertEqual(result.name, 'testcontributor')
        response = self.client.post(
            '/video_completion_contributor/{0}/'.format(video.slug),
            data={'action': 'modify',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_contributor')
        response = self.client.post(
            '/video_completion_contributor/{0}/'.format(video.slug),
            data={'action': 'save',
                  'name': 'testcontributor2',
                  'role': 'editor',
                  'video': 1,
                  'email_address': 'test@test.com',
                  'weblink': '',
                  'contributor_id': result.id
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_contributor')
        self.assertContains(response, 'testcontributor2')
        self.assertContains(response, _('editor'))
        result = Contributor.objects.get(id=1)
        self.assertEqual(result.name, 'testcontributor2')

        print(" ---> test_video_completion_contributor_edit : OK!")

    def test_video_completion_contributor_delete(self):
        video = Video.objects.get(id=1)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_contributor/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_contributor')
        response = self.client.post(
            '/video_completion_contributor/{0}/'.format(video.slug),
            data={'action': 'save',
                  'name': 'testcontributor',
                  'role': 'author',
                  'video': 1,
                  'email_address': 'test@test.com',
                  'weblink': '',
                  'contributor_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_contributor')
        result = Contributor.objects.get(id=1)
        self.assertEqual(result.name, 'testcontributor')
        response = self.client.post(
            '/video_completion_contributor/{0}/'.format(video.slug),
            data={'action': 'delete',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        result = Contributor.objects.all()
        self.assertFalse(result)

        print(" ---> test_video_completion_contributor_delete : OK!")


class CompletionTrackViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        site = Site.objects.get(id=1)
        staff = User.objects.create(
            username='staff', password='azerty', is_staff=True)
        staff.set_password('hello')
        staff.save()
        if FILEPICKER:
            UserFolder.objects.create(owner=staff, name='Home')
        vid = Video.objects.create(
            title='videotest2',
            owner=staff,
            video='test.mp4',
            type=Type.objects.get(id=1)
        )
        vid.sites.add(site)
        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_track(self):
        video = Video.objects.get(id=1)
        response = self.client.get(
            '/video_completion_track/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.get(
            '/video_completion_track/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'videotest2')
        self.assertContains(response, 'list_contributor')
        self.assertContains(response, 'list_track')
        self.assertContains(response, 'list_document')
        self.assertContains(response, 'list_overlay')

        print(" [ BEGIN COMPLETION_TRACK VIEWS ] ")
        print(" ---> test_video_completion_track : OK!")

    def test_video_completion_track_new(self):
        video = Video.objects.get(id=1)
        user = authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_track/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_track')
        testfile = SimpleUploadedFile(
            name='testfile.vtt',
            content=open(
                './pod/completion/tests/testfile.vtt', 'rb').read(),
            content_type='text/plain')
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name='testvtt',
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile
            )
        else:
            document = CustomFileModel.objects.create(
                file=testfile
            )
        response = self.client.post(
            '/video_completion_track/{0}/'.format(video.slug),
            data={'action': 'save',
                  'kind': 'subtitles',
                  'lang': 'fr',
                  'src': document.id,
                  'video': 1,
                  'track_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'list_track')
        result = Track.objects.get(id=1)
        self.assertEqual(result.kind, 'subtitles')
        self.assertTrue('testfile' in result.src.name)
        # self.assertEqual(result.src.name, 'testfile')

        print(" ---> test_video_completion_track_new : OK!")
        print(" [ END COMPLETION_TRACK VIEWS ] ")

    def test_video_completion_track_edit(self):
        video = Video.objects.get(id=1)
        user = authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_track/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_track')
        testfile = SimpleUploadedFile(
            name='testfile.vtt',
            content=open(
                './pod/completion/tests/testfile.vtt', 'rb').read(),
            content_type='text/plain')
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name='testvtt',
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile
            )
        else:
            document = CustomFileModel.objects.create(
                file=testfile
            )
        response = self.client.post(
            '/video_completion_track/{0}/'.format(video.slug),
            data={'action': 'save',
                  'kind': 'subtitles',
                  'lang': 'fr',
                  'src': document.id,
                  'video': 1,
                  'track_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_track')
        result = Track.objects.get(id=1)
        self.assertTrue('testfile' in result.src.name)
        # self.assertEqual(result.src.name, 'testfile')
        response = self.client.post(
            '/video_completion_track/{0}/'.format(video.slug),
            data={'action': 'modify',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_track')
        response = self.client.post(
            '/video_completion_track/{0}/'.format(video.slug),
            data={'action': 'save',
                  'kind': 'captions',
                  'lang': 'de',
                  'src': document.id,
                  'video': 1,
                  'track_id': result.id
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_track')
        result = Track.objects.get(id=1)
        self.assertEqual(result.kind, 'captions')
        self.assertEqual(result.lang, 'de')

        print(" ---> test_video_completion_track_edit : OK!")

    def test_video_completion_track_delete(self):
        video = Video.objects.get(id=1)
        user = authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_track/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_track')
        testfile = SimpleUploadedFile(
            name='testfile.vtt',
            content=open(
                './pod/completion/tests/testfile.vtt', 'rb').read(),
            content_type='text/plain')
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name='testvtt',
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile
            )
        else:
            document = CustomFileModel.objects.create(
                file=testfile
            )
        response = self.client.post(
            '/video_completion_track/{0}/'.format(video.slug),
            data={'action': 'save',
                  'kind': 'subtitles',
                  'lang': 'fr',
                  'src': document.id,
                  'video': 1,
                  'track_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_track')
        result = Track.objects.get(id=1)
        self.assertTrue('testfile' in result.src.name)
        # self.assertEqual(result.src.name, 'testfile')
        response = self.client.post(
            '/video_completion_track/{0}/'.format(video.slug),
            data={'action': 'delete',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        result = Track.objects.all()
        self.assertFalse(result)

        print(" ---> test_video_completion_track_delete : OK!")


class CompletionDocumentViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        site = Site.objects.get(id=1)
        staff = User.objects.create(
            username='staff', password='azerty', is_staff=True)
        staff.set_password('hello')
        staff.save()
        if FILEPICKER:
            UserFolder.objects.create(owner=staff, name='Home')
        vid = Video.objects.create(
            title='videotest2',
            owner=staff,
            video='test.mp4',
            type=Type.objects.get(id=1)
        )
        vid.sites.add(site)
        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_document(self):
        video = Video.objects.get(id=1)
        response = self.client.get(
            '/video_completion_document/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.get(
            '/video_completion_document/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'videotest2')
        self.assertContains(response, 'list_contributor')
        self.assertContains(response, 'list_track')
        self.assertContains(response, 'list_document')
        self.assertContains(response, 'list_overlay')

        print(" [ BEGIN COMPLETION_DOCUMENT VIEWS ] ")
        print(" ---> test_video_completion_document : OK!")

    def test_video_completion_document_new(self):
        video = Video.objects.get(id=1)
        user = authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_document/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_document')
        testfile = SimpleUploadedFile(
            name='testfile.vtt',
            content=open(
                './pod/completion/tests/testfile.vtt', 'rb').read(),
            content_type='text/plain')
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name='testfile',
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile
            )
        else:
            document = CustomFileModel.objects.create(
                file=testfile
            )
        response = self.client.post(
            '/video_completion_document/{0}/'.format(video.slug),
            data={'action': 'save',
                  'document': document.id,
                  'video': 1,
                  'track_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'list_document')
        result = Document.objects.get(id=1)
        # self.assertEqual(result.document.name, 'testfile')
        self.assertTrue('testfile' in result.document.name)

        print(" ---> test_video_completion_document_new : OK!")
        print(" [ END COMPLETION_DOCUMENT VIEWS ] ")

    def test_video_completion_document_edit(self):
        video = Video.objects.get(id=1)
        user = authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_document/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_document')
        testfile = SimpleUploadedFile(
            name='testfile.vtt',
            content=open(
                './pod/completion/tests/testfile.vtt', 'rb').read(),
            content_type='text/plain')
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name='testfile',
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile
            )
        else:
            document = CustomFileModel.objects.create(
                file=testfile
            )
        response = self.client.post(
            '/video_completion_document/{0}/'.format(video.slug),
            data={'action': 'save',
                  'document': document.id,
                  'video': 1,
                  'track_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'list_document')
        result = Document.objects.get(id=1)
        # self.assertEqual(result.document.name, 'testfile')
        self.assertTrue('testfile' in result.document.name)
        response = self.client.post(
            '/video_completion_document/{0}/'.format(video.slug),
            data={'action': 'modify',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_document')
        testfile = SimpleUploadedFile(
            name='testfile2.vtt',
            content=open(
                './pod/completion/tests/testfile.vtt', 'rb').read(),
            content_type='text/plain')
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name='testfile2',
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile
            )
        else:
            document = CustomFileModel.objects.create(
                file=testfile
            )
        response = self.client.post(
            '/video_completion_document/{0}/'.format(video.slug),
            data={'action': 'save',
                  'document': document.id,
                  'video': 1,
                  'document_id': result.id
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_document')
        result = Document.objects.get(id=1)
        # self.assertEqual(result.document.name, 'testfile2')
        self.assertTrue('testfile2' in result.document.name)
        print(" ---> test_video_completion_document_edit : OK!")

    def test_video_completion_document_delete(self):
        video = Video.objects.get(id=1)
        user = authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_document/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_document')
        testfile = SimpleUploadedFile(
            name='testfile.vtt',
            content=open(
                './pod/completion/tests/testfile.vtt', 'rb').read(),
            content_type='text/plain')
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name='testfile',
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile
            )
        else:
            document = CustomFileModel.objects.create(
                file=testfile
            )
        response = self.client.post(
            '/video_completion_document/{0}/'.format(video.slug),
            data={'action': 'save',
                  'document': document.id,
                  'video': 1,
                  'track_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_document')
        result = Document.objects.get(id=1)
        # self.assertEqual(result.document.name, 'testfile')
        self.assertTrue('testfile' in result.document.name)
        response = self.client.post(
            '/video_completion_document/{0}/'.format(video.slug),
            data={'action': 'delete',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        result = Document.objects.all()
        self.assertFalse(result)

        print(" ---> test_video_completion_document_delete : OK!")


class CompletionOverlayViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        staff = User.objects.create(
            username='staff', password='azerty', is_staff=True)
        staff.set_password('hello')
        staff.save()
        Video.objects.create(
            title='videotest2',
            owner=staff,
            video='test.mp4',
            duration=3,
            type=Type.objects.get(id=1)
        )
        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_overlay(self):
        video = Video.objects.get(id=1)
        response = self.client.get(
            '/video_completion_overlay/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.get(
            '/video_completion_overlay/{0}/'.format(video.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'videotest2')
        self.assertContains(response, 'list_contributor')
        self.assertContains(response, 'list_track')
        self.assertContains(response, 'list_document')
        self.assertContains(response, 'list_overlay')

        print(" [ BEGIN COMPLETION_OVERLAY VIEWS ] ")
        print(" ---> test_video_completion_overlay : OK!")

    def test_video_completion_overlay_new(self):
        video = Video.objects.get(id=1)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_overlay/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_overlay')
        response = self.client.post(
            '/video_completion_overlay/{0}/'.format(video.slug),
            data={'action': 'save',
                  'title': 'testoverlay',
                  'time_start': 1,
                  'time_end': 2,
                  'content': 'testoverlay',
                  'position': 'bottom-right',
                  'background': 'on',
                  'video': 1,
                  'overlay_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'list_overlay')
        result = Overlay.objects.get(id=1)
        self.assertEqual(result.title, 'testoverlay')
        self.assertEqual(result.content, 'testoverlay')

        print(" ---> test_video_completion_overlay_new : OK!")
        print(" [ END COMPLETION_OVERLAY VIEWS ] ")

    def test_video_completion_overlay_edit(self):
        video = Video.objects.get(id=1)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_overlay/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_overlay')
        response = self.client.post(
            '/video_completion_overlay/{0}/'.format(video.slug),
            data={'action': 'save',
                  'title': 'testoverlay',
                  'time_start': 1,
                  'time_end': 2,
                  'content': 'testoverlay',
                  'position': 'bottom-right',
                  'background': 'on',
                  'video': 1,
                  'overlay_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'video_completion.html')
        self.assertContains(response, 'list_overlay')
        result = Overlay.objects.get(id=1)
        self.assertEqual(result.title, 'testoverlay')
        response = self.client.post(
            '/video_completion_overlay/{0}/'.format(video.slug),
            data={'action': 'modify',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_overlay')
        response = self.client.post(
            '/video_completion_overlay/{0}/'.format(video.slug),
            data={'action': 'save',
                  'title': 'testoverlay2',
                  'time_start': 1,
                  'time_end': 3,
                  'content': 'testoverlay',
                  'position': 'bottom-left',
                  'background': 'on',
                  'video': 1,
                  'overlay_id': result.id
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_overlay')
        result = Overlay.objects.get(id=1)
        self.assertEqual(result.title, 'testoverlay2')
        self.assertEqual(result.time_end, 3)
        self.assertEqual(result.position, 'bottom-left')

        print(" ---> test_video_completion_overlay_edit : OK!")

    def test_video_completion_overlay_delete(self):
        video = Video.objects.get(id=1)
        authenticate(username='staff', password='hello')
        login = self.client.login(username='staff', password='hello')
        self.assertTrue(login)
        response = self.client.post(
            '/video_completion_overlay/{0}/'.format(video.slug),
            data={'action': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form_overlay')
        response = self.client.post(
            '/video_completion_overlay/{0}/'.format(video.slug),
            data={'action': 'save',
                  'title': 'testoverlay',
                  'time_start': 1,
                  'time_end': 2,
                  'content': 'testoverlay',
                  'position': 'bottom-right',
                  'background': 'on',
                  'video': 1,
                  'overlay_id': None
                  })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'list_overlay')
        result = Overlay.objects.get(id=1)
        self.assertEqual(result.title, 'testoverlay')
        response = self.client.post(
            '/video_completion_overlay/{0}/'.format(video.slug),
            data={'action': 'delete',
                  'id': result.id})
        self.assertEqual(response.status_code, 200)
        result = Overlay.objects.all()
        self.assertFalse(result)

        print(" ---> test_video_completion_overlay_delete : OK!")
