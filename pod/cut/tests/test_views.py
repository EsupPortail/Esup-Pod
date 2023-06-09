"""
Unit tests for CutVideo views
"""
from django.test import TestCase
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from pod.video.models import Video, Type
from django.contrib.sites.models import Site
from django.urls import reverse


class CutVideoViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        owner = User.objects.create(username="test", password="azerty", is_staff=True)
        owner.set_password("hello")
        owner.save()
        owner2 = User.objects.create(username="test2", password="azerty")
        owner2.set_password("hello")
        owner2.save()
        vid = Video.objects.create(
            title="videotest",
            owner=owner,
            video="test.mp4",
            duration=20,
            type=Type.objects.get(id=1),
        )

        owner.owner.sites.add(Site.objects.get_current())
        owner.owner.save()

        owner2.owner.sites.add(Site.objects.get_current())
        owner2.owner.save()

        vid.sites.add(site)

    def test_video_cut_owner(self):
        video = Video.objects.get(id=1)
        url = reverse("video:cut:video_cut", kwargs={"slug": video.slug})

        self.user = User.objects.get(username="test")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        authenticate(username="test2", password="hello")
        login = self.client.login(username="test2", password="hello")
        self.assertTrue(login)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # forbidden

        print(" ---> test_video_cut_owner: OK!")
        print(" [ END CUT VIEWS ] ")
