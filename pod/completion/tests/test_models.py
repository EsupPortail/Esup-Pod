"""
Unit tests for completion models.

Test with `python manage.py test pod.completion.tests.test_models`
"""

import base64

from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from pod.video.models import Video
from pod.video.models import Type
from pod.completion.models import Contributor
from pod.completion.models import Document
from pod.completion.models import Overlay
from pod.completion.models import Track
from datetime import datetime

if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel


class ContributorModelTestCase(TestCase):
    """Test case for Pod completion model."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up general data for all ContributoModel tests."""
        self.site = Site.objects.get(id=1)
        owner = User.objects.create(username="test")
        video_type = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video",
            type=video_type,
            owner=owner,
            video="test.mp4",
        )
        video.sites.add(self.site)
        Contributor.objects.create(
            video=video,
            name="contributor",
            email_address="contributor@pod.com",
            role="actor",
            weblink="http://pod.com",
        )
        Contributor.objects.create(video=video, name="contributor2")

    def test_attributs_full(self) -> None:
        """Test contributor with all attributes."""
        contributor = Contributor.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(contributor.video, video)
        self.assertEqual(contributor.name, "contributor")
        self.assertEqual(contributor.email_address, "contributor@pod.com")
        self.assertEqual(contributor.role, "actor")
        self.assertEqual(contributor.weblink, "http://pod.com")

        print(" ---> test_attributs_full: OK! --- ContributorModel")

    def test_attributs(self) -> None:
        """Test contributor with some empty attributes."""
        contributor = Contributor.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(contributor.video, video)
        self.assertEqual(contributor.name, "contributor2")
        self.assertEqual(contributor.email_address, "")
        self.assertEqual(contributor.role, "author")
        self.assertEqual(contributor.weblink, None)

        print(" [ BEGIN COMPLETION_TEST_MODELS ] ")
        print(" ---> test_attributs: OK! --- ContributorModel")

    def test_bad_attributs(self) -> None:
        """Test contributor with some bad attributes."""
        video = Video.objects.get(id=1)
        contributor = Contributor()
        contributor.video = video
        contributor.role = "actor"
        # A contributor must have a name
        self.assertRaises(ValidationError, contributor.clean)
        contributor.name = "t"
        # Contributor's name must have at least 2 chars
        self.assertRaises(ValidationError, contributor.clean)
        contributor.name = "test"
        contributor.role = None
        # Contributor's role can't be None
        self.assertRaises(ValidationError, contributor.clean)
        contributor.role = "actor"
        # Contributor's weblink cannot have more than 200 chars
        contributor.weblink = "x" * 201
        self.assertRaises(ValidationError, contributor.clean)

        print(" ---> test_bad_attributs: OK! --- ContributorModel")

    def test_same(self) -> None:
        video = Video.objects.get(id=1)
        contributor = Contributor()
        contributor.video = video
        contributor.name = "contributor"
        contributor.role = "actor"
        self.assertRaises(ValidationError, contributor.clean)

        print(" ---> test_same: OK! --- ContributorModel")

    def test_delete(self) -> None:
        Contributor.objects.get(id=1).delete()
        Contributor.objects.get(id=2).delete()
        self.assertTrue(Contributor.objects.all().count() == 0)

        print(" ---> test_delete: OK! --- ContributorModel")

    def test_sites_property(self) -> None:
        """Test the sites property of the Contributor model."""
        contributor = Contributor.objects.get(id=1)
        self.assertEqual(contributor.sites, Video.objects.get(id=1).sites)
        print(" ---> test_sites_property: OK! --- ContributorModel")

    def test_str(self) -> None:
        """Test the sites property of the Contributor model when the video is deleted."""
        contributor = Contributor.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(
            str(contributor),
            f"Video:{video} - Name:{contributor.name} - Role:{contributor.role}",
        )
        print(" ---> test_str: OK! --- ContributorModel")

    def test_get_base_mail(self) -> None:
        """Test the get_base_mail method of the Contributor model."""
        contributor = Contributor.objects.get(id=1)
        self.assertEqual(
            contributor.get_base_mail(),
            base64.b64encode(contributor.email_address.encode()).decode("utf-8"),
        )
        print(" ---> test_get_base_mail: OK! --- ContributorModel")

    def test_get_noscript_mail(self) -> None:
        """Test the get_noscript_mail method of the Contributor model."""
        contributor = Contributor.objects.get(id=1)
        self.assertEqual(contributor.get_noscript_mail(), "contributor__AT__pod.com")


class DocumentModelTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        owner = User.objects.create(username="test")
        videotype = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video", type=videotype, owner=owner, video="test.mp4"
        )
        testfile = SimpleUploadedFile(
            name="testfile.vtt",
            content=open("./pod/completion/tests/testfile.vtt", "rb").read(),
            content_type="text/plain",
        )
        if FILEPICKER:
            home = UserFolder.objects.create(name="Home", owner=owner)
            file = CustomFileModel.objects.create(
                name="testfile",
                uploaded_at=datetime.now(),
                created_by=owner,
                folder=home,
                file=testfile,
            )
        else:
            file = CustomFileModel.objects.create(file=testfile)
        Document.objects.create(video=video, document=file)
        Document.objects.create(video=video)

    def test_attributs_full(self) -> None:
        document = Document.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(document.video, video)
        if FILEPICKER:
            self.assertTrue(document.document.name, "testfile")
        else:
            self.assertTrue(document.document.name, "testfile.txt")

        print(" ---> test_attributs_full: OK! --- DocumentModel")

    def test_attributs(self) -> None:
        document = Document.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(document.video, video)
        self.assertEqual(document.document, None)

        print(" ---> test_attributs: OK! --- DocumentModel")

    def test_delete(self) -> None:
        Document.objects.get(id=1).delete()
        Document.objects.get(id=2).delete()
        self.assertTrue(Document.objects.all().count() == 0)

        print(" ---> test_delete: OK! --- DocumentModel")

    def test_sites_property(self) -> None:
        """Test the sites property of the Contributor model."""
        document = Document.objects.get(id=1)
        self.assertEqual(document.sites, Video.objects.get(id=1).sites)
        print(" ---> test_sites_property: OK! --- DocumentModel")

    def test_str(self) -> None:
        """Test the __str__ method of the Document model."""
        document = Document.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(
            str(document), f"Document: {document.document.name} - Video: {video}"
        )
        print(" ---> test_str: OK! --- DocumentModel")

    def test_verify_document(self) -> None:
        """Test the verify_document method of the Document model."""
        document = Document.objects.get(id=1)
        document.document = None
        document.save()
        self.assertIn(_("Please enter a document."), document.verify_document())
        print(" ---> test_verify_document: OK! --- DocumentModel")


class OverlayModelTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        owner = User.objects.create(username="test")
        videotype = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video",
            type=videotype,
            owner=owner,
            video="test.mp4",
            duration=10,
        )
        Overlay.objects.create(
            video=video,
            title="overlay",
            content="test",
            time_start=1,
            time_end=5,
            position="top-left",
        )
        Overlay.objects.create(video=video, title="overlay2", content="test")

    def test_attributs_full(self) -> None:
        overlay = Overlay.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(overlay.video, video)
        self.assertEqual(overlay.title, "overlay")
        self.assertEqual(overlay.content, "test")
        self.assertEqual(overlay.time_start, 1)
        self.assertEqual(overlay.time_end, 5)
        self.assertEqual(overlay.position, "top-left")

        print(" ---> test_attributs_full: OK! --- OverlayModel")

    def test_attributs(self) -> None:
        overlay = Overlay.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(overlay.video, video)
        self.assertEqual(overlay.title, "overlay2")
        self.assertEqual(overlay.content, "test")
        self.assertEqual(overlay.time_start, 1)
        self.assertEqual(overlay.time_end, 2)
        self.assertEqual(overlay.position, "bottom-right")
        self.assertTrue(overlay.background)

        print(" ---> test_attributs: OK! --- OverlayModel")

    def test_title(self) -> None:
        video = Video.objects.get(id=1)
        overlay = Overlay()
        overlay.video = video
        overlay.content = "test"
        self.assertRaises(ValidationError, overlay.clean)
        overlay.title = "t"
        self.assertRaises(ValidationError, overlay.clean)

        print(" ---> test_title: OK! --- OverlayModel")

    def test_times(self) -> None:
        video = Video.objects.get(id=1)
        overlay = Overlay()
        overlay.video = video
        overlay.title = "test"
        overlay.content = "test"
        overlay.time_start = 7
        overlay.time_end = 6
        self.assertRaises(ValidationError, overlay.clean)
        overlay.time_end = 11
        self.assertRaises(ValidationError, overlay.clean)
        overlay.time_end = 7
        self.assertRaises(ValidationError, overlay.clean)

        print(" ---> test_times: OK! --- OverlayModel")

    def test_overlap(self) -> None:
        video = Video.objects.get(id=1)
        overlay = Overlay()
        overlay.video = video
        overlay.title = "test"
        overlay.content = "test"
        overlay.time_start = 2
        overlay.time_end = 3
        self.assertRaises(ValidationError, overlay.clean)

        print(" ---> test_overlap: OK! --- OverlayModel")

    def test_delete(self) -> None:
        Overlay.objects.get(id=1).delete()
        Overlay.objects.get(id=2).delete()
        self.assertTrue(Overlay.objects.all().count() == 0)

        print(" ---> test_delete: OK! --- OverlayModel")


class TrackModelTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        owner = User.objects.create(username="test")
        videotype = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video", type=videotype, owner=owner, video="test.mp4"
        )
        testfile = SimpleUploadedFile(
            name="testfile.vtt",
            content=open("./pod/completion/tests/testfile.vtt", "rb").read(),
            content_type="text/plain",
        )
        if FILEPICKER:
            home = UserFolder.objects.create(name="Home", owner=owner)
            file = CustomFileModel.objects.create(
                name="testfile",
                uploaded_at=datetime.now(),
                created_by=owner,
                folder=home,
                file=testfile,
            )
        else:
            file = CustomFileModel.objects.create(file=testfile)
        Track.objects.create(video=video, lang="fr", kind="captions", src=file)
        Track.objects.create(video=video, lang="en")

    def test_attributs_full(self) -> None:
        track = Track.objects.get(id=1)
        video = Video.objects.get(id=1)
        self.assertEqual(track.video, video)
        self.assertEqual(track.lang, "fr")
        self.assertEqual(track.kind, "captions")
        self.assertTrue("testfile" in track.src.name)
        # self.assertEqual(track.src.name, 'testfile')

        print(" ---> test_attributs_full: OK! --- TrackModel")

    def test_attributs(self) -> None:
        track = Track.objects.get(id=2)
        video = Video.objects.get(id=1)
        self.assertEqual(track.video, video)
        self.assertEqual(track.lang, "en")
        self.assertEqual(track.kind, "subtitles")
        self.assertEqual(track.src, None)

        print(" ---> test_attributs: OK! --- TrackModel")

    def test_bad_attributs(self) -> None:
        track = Track.objects.get(id=1)
        track.kind = None
        self.assertRaises(ValidationError, track.clean)
        track.kind = "other"
        self.assertRaises(ValidationError, track.clean)
        track.kind = "captions"
        track.lang = None
        self.assertRaises(ValidationError, track.clean)
        track.lang = "en"
        track.src = None
        self.assertRaises(ValidationError, track.clean)

        print(" ---> test_bad_attributs: OK! --- TrackModel")

    def test_same(self) -> None:
        video = Video.objects.get(id=1)
        track = Track()
        track.video = video
        track.kind = "captions"
        track.lang = "en"
        self.assertRaises(ValidationError, track.clean)

        print(" ---> test_same: OK! --- TrackModel")
        print(" [ END COMPLETION_TEST_MODELS ] ")

    def test_delete(self):
        Track.objects.get(id=1).delete()
        Track.objects.get(id=2).delete()
        self.assertTrue(Overlay.objects.all().count() == 0)

        print(" ---> test_delete: OK! --- TrackModel")
