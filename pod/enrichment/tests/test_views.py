# gitguardian:ignore

"""
Unit tests for enrichment views.
"""
from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.urls import reverse
from pod.playlist.models import Playlist
from pod.video.models import Video, Type
from ..models import Enrichment
from django.contrib.sites.models import Site

__PWD__ = "thisisnotpassword"


class EnrichmentViewsTestCase(TestCase):
    """TestCase for enrichment application views."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Set up the tests."""
        site = Site.objects.get(id=1)
        owner = User.objects.create(username="test", password=__PWD__, is_staff=True)
        owner.set_password(__PWD__)
        owner.save()
        vid = Video.objects.create(
            title="videotest",
            owner=owner,
            video="test.mp4",
            duration=20,
            type=Type.objects.get(id=1),
        )
        owner.owner.sites.add(Site.objects.get_current())
        owner.owner.save()
        vid.sites.add(site)

    def test_video_enrichment(self):
        """Test the video edit enrichment page."""
        video = Video.objects.get(id=1)
        url = reverse("enrichment:edit_enrichment", kwargs={"slug": video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        authenticate(username="test", password=__PWD__)
        login = self.client.login(username="test", password=__PWD__)
        self.assertTrue(login)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "enrichment/edit_enrichment.html")
        self.assertContains(response, "videotest")
        # self.assertContains(response, "list_enrich")

        print(" ---> test_video_enrichment: OK!")

    def test_video_enrichment_new(self):
        """Test the video create enrichment page."""
        video = Video.objects.get(id=1)
        authenticate(username="test", password=__PWD__)
        login = self.client.login(username="test", password=__PWD__)
        self.assertTrue(login)
        url = reverse("enrichment:edit_enrichment", kwargs={"slug": video.slug})
        response = self.client.post(url, data={"action": "new"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "enrichment/edit_enrichment.html")
        self.assertContains(response, "videotest")
        # self.assertContains(response, "list_enrich")
        self.assertContains(response, "form_enrich")
        response = self.client.post(
            url,
            data={
                "action": "save",
                "video": 1,
                "title": "testenrich",
                "start": 1,
                "end": 2,
                "type": "weblink",
                "weblink": "http://test.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        result = Enrichment.objects.all()
        self.assertTrue(result)
        self.assertTemplateUsed("enrichment/edit_enrichment.html")
        self.assertContains(response, "videotest")
        # self.assertContains(response, "list_enrich")
        # self.assertContains(response, "testenrich")

        print(" ---> test_video_enrichment_new: OK!")
        print(" [ END ENRICHMENT VIEWS ] ")

    def test_video_enrichment_edit(self):
        """Test the video edit enrichment page."""
        video = Video.objects.get(id=1)
        authenticate(username="test", password=__PWD__)
        login = self.client.login(username="test", password=__PWD__)
        self.assertTrue(login)
        url = reverse("enrichment:edit_enrichment", kwargs={"slug": video.slug})
        response = self.client.post(
            url,
            data={
                "action": "save",
                "video": 1,
                "title": "testenrich",
                "start": 1,
                "end": 2,
                "type": "weblink",
                "weblink": "http://test.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        result = Enrichment.objects.all()
        self.assertTrue(result)
        result = Enrichment.objects.get(id=1)
        response = self.client.post(
            url,
            data={
                "action": "save",
                "enrich_id": result.id,
                "video": 1,
                "title": "testenrich2",
                "start": 2,
                "end": 3,
                "type": "weblink",
                "weblink": "http://test.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("enrichment/edit_enrichment.html")
        self.assertContains(response, "videotest")
        # self.assertContains(response, "list_enrich")
        # self.assertContains(response, "testenrich2")

        print(" ---> test_video_enrichment_edit: OK!")

    def test_video_enrichment_delete(self):
        """Test the video delete enrichment."""
        video = Video.objects.get(id=1)
        authenticate(username="test", password=__PWD__)
        login = self.client.login(username="test", password=__PWD__)
        self.assertTrue(login)
        url = reverse("enrichment:edit_enrichment", kwargs={"slug": video.slug})
        response = self.client.post(
            url,
            data={
                "action": "save",
                "video": 1,
                "title": "testenrich",
                "start": 1,
                "end": 2,
                "type": "weblink",
                "weblink": "http://test.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        result = Enrichment.objects.all()
        self.assertTrue(result)
        result = Enrichment.objects.get(id=1)
        response = self.client.post(url, data={"action": "delete", "id": result.id})
        self.assertEqual(response.status_code, 200)
        result = Enrichment.objects.all()
        self.assertFalse(result)

        print(" [ BEGIN ENRICHMENT VIEWS ] ")
        print(" ---> test_video_enrichment_delete: OK!")


class VideoEnrichmentViewTestCase(TestCase):
    """This TestCase test the video_enrichment view."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Set up the tests."""
        site = Site.objects.get(id=1)
        self.user = User.objects.create(username="test", password=__PWD__, is_staff=True)
        self.student = User.objects.create(username="test_student", password=__PWD__)
        self.video = Video.objects.create(
            title="videotest",
            owner=self.user,
            video="test.mp4",
            duration=20,
            type=Type.objects.get(id=1),
        )
        self.video.sites.add(site)

    def test_access_video_enrichment(self):
        """Test the video enrichment access."""
        self.client.force_login(self.user)
        url = reverse('enrichment:video_enrichment', kwargs={'slug': self.video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'enrichment/video_enrichment.html')

    def test_invalid_video_slug(self):
        """Test the view with invalid slug."""
        url = reverse('enrichment:video_enrichment', kwargs={'slug': 'invalid-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_private_playlist_access(self):
        """Test if a random user can't access to a private playlist."""
        self.client.force_login(self.student)
        playlist = Playlist.objects.create(
            name="Private playlist",
            visibility="private",
            owner=self.user,
        )
        url = reverse('enrichment:video_enrichment', kwargs={'slug': self.video.slug}) + f'?playlist={playlist.slug}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
