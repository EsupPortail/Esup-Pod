"""
Unit tests for completion models
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from pod.video.models import Video
from pod.completion.models import Contributor
from pod.completion.models import Document
from pod.completion.models import Overlay
from pod.completion.models import Track
try:
    __import__('pod.filepicker')
    FILEPICKER = True
    from pod.filepicker.models import CustomFileModel
    from pod.filepicker.models import UserDirectory
except ImportError:
    FILEPICKER = False
    pass
from datetime import datetime


class ContributorModelTestCase(TestCase):

    def setUp(self):
        owner = User.objects.create(username='test')
        video = Video.objects.create(
            title='video',
            owner=owner,
            video='test.mp4'
        )
        Contributor.objects.create(
            video=video,
            name='contributor',
            email_address='contributor@pod.com',
            role='actor',
            weblink='http://pod.com'
        )
        Contributor.objects.create(
            video=video,
            name='contributor2'
        )

    def test_attributs_full(self):
        contributor = Contributor.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(contributor.video, video)
        self.assertEqual(contributor.name, 'contributor')
        self.assertEqual(contributor.email_address, 'contributor@pod.com')
        self.assertEqual(contributor.role, 'actor')
        self.assertEqual(contributor.weblink, 'http://pod.com')

        print(" ---> test_attributs_full : OK ! --- ContributorModel")

    def test_attributs(self):
        contributor = Contributor.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(contributor.video, video)
        self.assertEqual(contributor.name, 'contributor2')
        self.assertEqual(contributor.email_address, '')
        self.assertEqual(contributor.role, 'author')
        self.assertEqual(contributor.weblink, None)

        print(" [ BEGIN COMPLETION_TEST_MODELS ] ")
        print(" ---> test_attributs : OK ! --- ContributorModel")

    def test_clean(self):
        Contributor.objects.get(id=1).delete()
        Contributor.objects.get(id=2).delete()
        self.assertTrue(Contributor.objects.all().count() == 0)


class DocumentModelTestCase(TestCase):

    def setUp(self):
        owner = User.objects.create(username='test')
        video = Video.objects.create(
            title='video',
            owner=owner,
            video='test.mp4'
        )
        if FILEPICKER:
            testfile = SimpleUploadedFile(
                name='testfile.vtt',
                content=open(
                    './pod/completion/tests/testfile.vtt', 'rb').read(),
                content_type='text/plain')
            home = UserDirectory.objects.create(name='Home', owner=owner)
            file = CustomFileModel.objects.create(
                name='testfile',
                date_created=datetime.now(),
                date_modified=datetime.now(),
                created_by=owner,
                modified_by=owner,
                directory=home,
                file=testfile
            )
        else:
            file = SimpleUploadedFile(
                name='testfile.vtt',
                content=open(
                    './pod/completion/tests/testfile.vtt', 'rb').read(),
                content_type='text/plain')
        Document.objects.create(
            video=video,
            document=file)
        Document.objects.create(
            video=video
        )

    def test_attributs_full(self):
        document = Document.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(document.video, video)
        if FILEPICKER:
            self.assertTrue(document.document.name, 'testfile')
        else:
            self.assertTrue(document.document.name, 'testfile.txt')

        print(" ---> test_attributs_full : OK ! --- DocumentModel")

    def test_attributs(self):
        document = Document.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(document.video, video)
        self.assertEqual(document.document, None)

        print(" ---> test_attributs : OK ! --- DocumentModel")

    def test_clean(self):
        Document.objects.get(id=1).delete()
        Document.objects.get(id=2).delete()
        self.assertTrue(Document.objects.all().count() == 0)


class OverlayModelTestCase(TestCase):

    def setUp(self):
        owner = User.objects.create(username='test')
        video = Video.objects.create(
            title='video',
            owner=owner,
            video='test.mp4'
        )
        Overlay.objects.create(
            video=video,
            title='overlay',
            content='test',
            time_end=5,
            position='top-left'
        )
        Overlay.objects.create(
            video=video,
            title='overlay2',
            content='test'
        )

    def test_attributs_full(self):
        overlay = Overlay.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(overlay.video, video)
        self.assertEqual(overlay.title, 'overlay')
        self.assertEqual(overlay.content, 'test')
        self.assertEqual(overlay.time_end, 5)
        self.assertEqual(overlay.position, 'top-left')

        print(" ---> test_attributs_full : OK ! --- OverlayModel")

    def test_attributs(self):
        overlay = Overlay.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(overlay.video, video)
        self.assertEqual(overlay.title, 'overlay2')
        self.assertEqual(overlay.content, 'test')
        self.assertEqual(overlay.time_start, 1)
        self.assertEqual(overlay.time_end, 2)
        self.assertEqual(overlay.position, 'bottom-right')
        self.assertTrue(overlay.background)

        print(" ---> test_attributs : OK ! --- OverlayModel")

    def test_clean(self):
        Overlay.objects.get(id=1).delete()
        Overlay.objects.get(id=2).delete()
        self.assertTrue(Overlay.objects.all().count() == 0)


class TrackModelTestCase(TestCase):

    def setUp(self):
        owner = User.objects.create(username='test')
        video = Video.objects.create(
            title='video',
            owner=owner,
            video='test.mp4'
        )
        if FILEPICKER:
            testfile = SimpleUploadedFile(
                name='testfile.vtt',
                content=open(
                    './pod/completion/tests/testfile.vtt', 'rb').read(),
                content_type='text/plain')
            home = UserDirectory.objects.create(name='Home', owner=owner)
            file = CustomFileModel.objects.create(
                name='testfile',
                date_created=datetime.now(),
                date_modified=datetime.now(),
                created_by=owner,
                modified_by=owner,
                directory=home,
                file=testfile
            )
        else:
            file = SimpleUploadedFile(
                name='testfile.vtt',
                content=open(
                    './pod/completion/tests/testfile.vtt', 'rb').read(),
                content_type='text/plain')
        Track.objects.create(
            video=video,
            lang='fr',
            kind='captions',
            src=file
        )
        Track.objects.create(
            video=video,
            lang='en'
        )

    def test_attributs_full(self):
        track = Track.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(track.video, video)
        self.assertEqual(track.lang, 'fr')
        self.assertEqual(track.kind, 'captions')
        self.assertEqual(track.src.name, 'testfile')

        print(" ---> test_attributs_full : OK ! --- TrackModel")

    def test_attributs(self):
        track = Track.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(track.video, video)
        self.assertEqual(track.lang, 'en')
        self.assertEqual(track.kind, 'subtitles')
        self.assertEqual(track.src, None)

        print(" ---> test_attributs : OK ! --- TrackModel")

    def test_clean(self):
        Track.objects.get(id=1).delete()
        Track.objects.get(id=2).delete()
        self.assertTrue(Overlay.objects.all().count() == 0)
        print(" [ END COMPLETION_TEST_MODELS ] ")
