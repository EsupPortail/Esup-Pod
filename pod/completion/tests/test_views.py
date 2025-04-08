"""Esup-Pod unit tests for completion views.

test with `python manage.py test pod.completion.tests.test_views`
"""

from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from pod.video.models import Video, Type
from ..models import Contributor
from ..models import Document
from ..models import Overlay
from ..models import Track
from datetime import datetime
from django.contrib.sites.models import Site
from django.urls import reverse

if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel

# ggignore-start
# gitguardian:ignore
PWD = "azerty1234"  # nosec
# ggignore-end


class CompletionViewsTestCase(TestCase):
    """Test cases for the Pod video completion views."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up the CompletionViews test case."""
        site = Site.objects.get(id=1)
        user = User.objects.create(username="test")
        user.set_password(PWD)  # nosem
        user.save()
        staff = User.objects.create(username="staff", is_staff=True)
        staff.set_password(PWD)  # nosem
        staff.save()
        vid1 = Video.objects.create(
            title="videotest",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        vid1.sites.add(site)
        vid2 = Video.objects.create(
            title="videotest2",
            owner=staff,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        vid2.sites.add(site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_user(self) -> None:
        video = Video.objects.get(id=1)
        url = reverse("video:completion:video_completion", kwargs={"slug": video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        authenticate(username="test", password=PWD)
        login = self.client.login(username="test", password=PWD)
        self.assertTrue(login)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "videotest")
        self.assertContains(response, "list-contributor")

        print(" ---> test_video_completion_user: OK!")

    def test_video_completion_staff(self) -> None:
        video = Video.objects.get(id=2)
        url = reverse("video:completion:video_completion", kwargs={"slug": video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "videotest2")
        self.assertContains(response, "list-contributor")
        self.assertContains(response, "list-track")
        self.assertContains(response, "list-document")
        self.assertContains(response, "list-overlay")

        print(" ---> test_video_completion_staff: OK!")


class CompletionContributorViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up the CompletionContributorViews test case."""
        site = Site.objects.get(id=1)
        staff = User.objects.create(username="staff", is_staff=True)
        staff.set_password(PWD)  # nosem
        staff.save()
        vid = Video.objects.create(
            title="videotest2",
            owner=staff,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        vid.sites.add(site)
        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_contributor(self) -> None:
        video = Video.objects.get(id=1)
        url = reverse(
            "video:completion:video_completion_contributor", kwargs={"slug": video.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "videotest2")
        self.assertContains(response, "list-contributor")
        self.assertContains(response, "list-track")
        self.assertContains(response, "list-document")
        self.assertContains(response, "list-overlay")

        print(" [ BEGIN COMPLETION_CONTRIBUTOR VIEWS ] ")
        print(" ---> test_video_completion_contributor: OK!")

    def test_video_completion_contributor_new(self) -> None:
        video = Video.objects.get(id=1)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_contributor", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_contributor")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "name": "testcontributor",
                "role": "author",
                "video": 1,
                "email_address": "test@test.com",
                "weblink": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "list-contributor")
        self.assertContains(response, "testcontributor")
        self.assertContains(response, "test@test.com")

        result = Contributor.objects.get(id=1)
        self.assertEqual(result.name, "testcontributor")

        print(" ---> test_video_completion_contributor_new: OK!")
        print(" [ END COMPLETION_CONTRIBUTOR VIEWS ] ")

    def test_video_completion_contributor_edit(self) -> None:
        video = Video.objects.get(id=1)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_contributor", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_contributor")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "name": "testcontributor",
                "role": "author",
                "video": 1,
                "email_address": "test@test.com",
                "weblink": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-contributor")
        result = Contributor.objects.get(id=1)
        self.assertEqual(result.name, "testcontributor")
        response = self.client.post(
            url,
            data={"action": "modify", "id": result.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_contributor")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "name": "testcontributor2",
                "role": "editor",
                "video": 1,
                "email_address": "test@test.com",
                "weblink": "",
                "contributor_id": result.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-contributor")
        self.assertContains(response, "testcontributor2")
        self.assertContains(response, _("editor"))
        result = Contributor.objects.get(id=1)
        self.assertEqual(result.name, "testcontributor2")

        print(" ---> test_video_completion_contributor_edit: OK!")

    def test_video_completion_contributor_delete(self) -> None:
        video = Video.objects.get(id=1)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_contributor", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_contributor")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "name": "testcontributor",
                "role": "author",
                "video": 1,
                "email_address": "test@test.com",
                "weblink": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-contributor")

        result = Contributor.objects.get(id=1)
        self.assertEqual(result.name, "testcontributor")
        response = self.client.post(
            url,
            data={"action": "delete", "id": result.id},
        )
        self.assertEqual(response.status_code, 200)
        result = Contributor.objects.all()
        self.assertFalse(result)

        print(" ---> test_video_completion_contributor_delete: OK!")


class CompletionTrackViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up the CompletionTrackViews test case."""
        site = Site.objects.get(id=1)
        staff = User.objects.create(username="staff", is_staff=True)
        staff.set_password(PWD)  # nosem
        staff.save()
        if FILEPICKER:
            UserFolder.objects.create(owner=staff, name="Home")
        vid = Video.objects.create(
            title="videotest2",
            owner=staff,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        vid.sites.add(site)
        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_track(self) -> None:
        video = Video.objects.get(id=1)
        url = reverse(
            "video:completion:video_completion_track", kwargs={"slug": video.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "videotest2")
        self.assertContains(response, "list-contributor")
        self.assertContains(response, "list-track")
        self.assertContains(response, "list-document")
        self.assertContains(response, "list-overlay")

        print(" [ BEGIN COMPLETION_TRACK VIEWS ] ")
        print(" ---> test_video_completion_track: OK!")

    def test_video_completion_track_new(self) -> None:
        video = Video.objects.get(id=1)
        user = authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_track", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_track")
        testfile = SimpleUploadedFile(
            name="testfile.vtt",
            content=open("./pod/completion/tests/testfile.vtt", "rb").read(),
            content_type="text/plain",
        )
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name="testvtt",
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile,
            )
        else:
            document = CustomFileModel.objects.create(file=testfile)
        response = self.client.post(
            url,
            data={
                "action": "save",
                "kind": "subtitles",
                "lang": "fr",
                "src": document.id,
                "video": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "list-track")
        result = Track.objects.get(id=1)
        self.assertEqual(result.kind, "subtitles")
        self.assertTrue("testfile" in result.src.name)
        # self.assertEqual(result.src.name, 'testfile')

        print(" ---> test_video_completion_track_new: OK!")
        print(" [ END COMPLETION_TRACK VIEWS ] ")

    def test_video_completion_track_edit(self):
        video = Video.objects.get(id=1)
        user = authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_track", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_track")
        testfile = SimpleUploadedFile(
            name="testfile.vtt",
            content=open("./pod/completion/tests/testfile.vtt", "rb").read(),
            content_type="text/plain",
        )
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name="testvtt",
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile,
            )
        else:
            document = CustomFileModel.objects.create(file=testfile)
        response = self.client.post(
            url,
            data={
                "action": "save",
                "kind": "subtitles",
                "lang": "fr",
                "src": document.id,
                "video": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-track")
        result = Track.objects.get(id=1)
        self.assertTrue("testfile" in result.src.name)
        # self.assertEqual(result.src.name, 'testfile')
        response = self.client.post(
            url,
            data={"action": "modify", "id": result.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_track")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "kind": "captions",
                "lang": "de",
                "src": document.id,
                "video": 1,
                "track_id": result.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-track")
        result = Track.objects.get(id=1)
        self.assertEqual(result.kind, "captions")
        self.assertEqual(result.lang, "de")

        print(" ---> test_video_completion_track_edit: OK!")

    def test_video_completion_track_delete(self):
        video = Video.objects.get(id=1)
        user = authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_track", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_track")
        testfile = SimpleUploadedFile(
            name="testfile.vtt",
            content=open("./pod/completion/tests/testfile.vtt", "rb").read(),
            content_type="text/plain",
        )
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name="testvtt",
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile,
            )
        else:
            document = CustomFileModel.objects.create(file=testfile)
        response = self.client.post(
            url,
            data={
                "action": "save",
                "kind": "subtitles",
                "lang": "fr",
                "src": document.id,
                "video": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-track")
        result = Track.objects.get(id=1)
        self.assertTrue("testfile" in result.src.name)
        # self.assertEqual(result.src.name, 'testfile')
        response = self.client.post(
            url,
            data={"action": "delete", "id": result.id},
        )
        self.assertEqual(response.status_code, 200)
        result = Track.objects.all()
        self.assertFalse(result)

        print(" ---> test_video_completion_track_delete: OK!")


class CompletionDocumentViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up the CompletionDocumentViews test case."""
        site = Site.objects.get(id=1)
        staff = User.objects.create(username="staff", is_staff=True)
        staff.set_password(PWD)  # nosem
        staff.save()
        if FILEPICKER:
            UserFolder.objects.create(owner=staff, name="Home")
        vid = Video.objects.create(
            title="videotest2",
            owner=staff,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        vid.sites.add(site)
        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_document(self) -> None:
        video = Video.objects.get(id=1)
        url = reverse(
            "video:completion:video_completion_document", kwargs={"slug": video.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "videotest2")
        self.assertContains(response, "list-contributor")
        self.assertContains(response, "list-track")
        self.assertContains(response, "list-document")
        self.assertContains(response, "list-overlay")

        print(" [ BEGIN COMPLETION_DOCUMENT VIEWS ] ")
        print(" ---> test_video_completion_document: OK!")

    def test_video_completion_document_new(self) -> None:
        video = Video.objects.get(id=1)
        user = authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_document", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_document")
        testfile = SimpleUploadedFile(
            name="testfile.vtt",
            content=open("./pod/completion/tests/testfile.vtt", "rb").read(),
            content_type="text/plain",
        )
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name="testfile",
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile,
            )
        else:
            document = CustomFileModel.objects.create(file=testfile)
        response = self.client.post(
            url,
            data={
                "action": "save",
                "document": document.id,
                "video": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "list-document")
        result = Document.objects.get(id=1)
        # self.assertEqual(result.document.name, 'testfile')
        self.assertTrue("testfile" in result.document.name)

        print(" ---> test_video_completion_document_new: OK!")
        print(" [ END COMPLETION_DOCUMENT VIEWS ] ")

    def test_video_completion_document_edit(self) -> None:
        video = Video.objects.get(id=1)
        user = authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_document", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_document")
        testfile = SimpleUploadedFile(
            name="testfile.vtt",
            content=open("./pod/completion/tests/testfile.vtt", "rb").read(),
            content_type="text/plain",
        )
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name="testfile",
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile,
            )
        else:
            document = CustomFileModel.objects.create(file=testfile)
        response = self.client.post(
            url,
            data={
                "action": "save",
                "document": document.id,
                "video": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "list-document")
        result = Document.objects.get(id=1)
        # self.assertEqual(result.document.name, 'testfile')
        self.assertTrue("testfile" in result.document.name)
        response = self.client.post(
            url,
            data={"action": "modify", "id": result.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_document")
        testfile = SimpleUploadedFile(
            name="testfile2.vtt",
            content=open("./pod/completion/tests/testfile.vtt", "rb").read(),
            content_type="text/plain",
        )
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name="testfile2",
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile,
            )
        else:
            document = CustomFileModel.objects.create(file=testfile)
        response = self.client.post(
            url,
            data={
                "action": "save",
                "document": document.id,
                "video": 1,
                "id-instance-document": result.id,
                "private": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-document")
        result = Document.objects.get(id=1)
        # self.assertEqual(result.document.name, 'testfile2')
        self.assertTrue("testfile2" in result.document.name)
        print(" ---> test_video_completion_document_edit: OK!")

    def test_video_completion_document_delete(self) -> None:
        video = Video.objects.get(id=1)
        user = authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_document", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_document")
        testfile = SimpleUploadedFile(
            name="testfile.vtt",
            content=open("./pod/completion/tests/testfile.vtt", "rb").read(),
            content_type="text/plain",
        )
        if FILEPICKER:
            home = UserFolder.objects.get(id=1)
            document = CustomFileModel.objects.create(
                name="testfile",
                uploaded_at=datetime.now(),
                created_by=user,
                folder=home,
                file=testfile,
            )
        else:
            document = CustomFileModel.objects.create(file=testfile)
        response = self.client.post(
            url,
            data={
                "action": "save",
                "document": document.id,
                "video": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-document")
        result = Document.objects.get(id=1)
        # self.assertEqual(result.document.name, 'testfile')
        self.assertTrue("testfile" in result.document.name)
        response = self.client.post(
            url,
            data={"action": "delete", "id": result.id},
        )
        self.assertEqual(response.status_code, 200)
        result = Document.objects.all()
        self.assertFalse(result)

        print(" ---> test_video_completion_document_delete: OK!")


class CompletionOverlayViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up the CompletionOverlayViews test case."""
        staff = User.objects.create(username="staff", is_staff=True)
        staff.set_password(PWD)  # nosem
        staff.save()
        Video.objects.create(
            title="videotest2",
            owner=staff,
            video="test.mp4",
            duration=3,
            type=Type.objects.get(id=1),
        )
        staff.owner.sites.add(Site.objects.get_current())
        staff.owner.save()

    def test_video_completion_overlay(self) -> None:
        video = Video.objects.get(id=1)
        url = reverse(
            "video:completion:video_completion_overlay", kwargs={"slug": video.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "videotest2")
        self.assertContains(response, "list-contributor")
        self.assertContains(response, "list-track")
        self.assertContains(response, "list-document")
        self.assertContains(response, "list-overlay")

        print(" [ BEGIN COMPLETION_OVERLAY VIEWS ] ")
        print(" ---> test_video_completion_overlay: OK!")

    def test_video_completion_overlay_new(self) -> None:
        video = Video.objects.get(id=1)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_overlay", kwargs={"slug": video.slug}
        )
        response = self.client.post(url, data={"action": "new"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_overlay")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "title": "testoverlay",
                "time_start": 1,
                "time_end": 2,
                "content": "testoverlay",
                "position": "bottom-right",
                "background": "on",
                "video": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "list-overlay")

        result = Overlay.objects.get(id=1)
        self.assertEqual(result.title, "testoverlay")
        self.assertEqual(result.content, "testoverlay")

        print(" ---> test_video_completion_overlay_new: OK!")
        print(" [ END COMPLETION_OVERLAY VIEWS ] ")

    def test_video_completion_overlay_edit(self) -> None:
        video = Video.objects.get(id=1)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_overlay", kwargs={"slug": video.slug}
        )
        response = self.client.post(url, data={"action": "new"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_overlay")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "title": "testoverlay",
                "time_start": 1,
                "time_end": 2,
                "content": "testoverlay",
                "position": "bottom-right",
                "background": "on",
                "video": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_completion.html")
        self.assertContains(response, "list-overlay")
        result = Overlay.objects.get(id=1)
        self.assertEqual(result.title, "testoverlay")
        response = self.client.post(
            url,
            data={"action": "modify", "id": result.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_overlay")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "title": "testoverlay2",
                "time_start": 1,
                "time_end": 3,
                "content": "testoverlay",
                "position": "bottom-left",
                "background": "on",
                "video": 1,
                "overlay_id": result.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-overlay")
        result = Overlay.objects.get(id=1)
        self.assertEqual(result.title, "testoverlay2")
        self.assertEqual(result.time_end, 3)
        self.assertEqual(result.position, "bottom-left")

        print(" ---> test_video_completion_overlay_edit: OK!")

    def test_video_completion_overlay_delete(self) -> None:
        video = Video.objects.get(id=1)
        authenticate(username="staff", password=PWD)
        login = self.client.login(username="staff", password=PWD)
        self.assertTrue(login)
        url = reverse(
            "video:completion:video_completion_overlay", kwargs={"slug": video.slug}
        )
        response = self.client.post(
            url,
            data={"action": "new"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form_overlay")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "title": "testoverlay",
                "time_start": 1,
                "time_end": 2,
                "content": "testoverlay",
                "position": "bottom-right",
                "background": "on",
                "video": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "list-overlay")
        result = Overlay.objects.get(id=1)
        self.assertEqual(result.title, "testoverlay")
        response = self.client.post(
            url,
            data={"action": "delete", "id": result.id},
        )
        self.assertEqual(response.status_code, 200)
        result = Overlay.objects.all()
        self.assertFalse(result)

        print(" ---> test_video_completion_overlay_delete: OK!")
