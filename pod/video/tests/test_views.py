from django.test import Client
from django.test import TestCase, override_settings, TransactionTestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from .. import views
from ..models import Type
from ..models import Theme
from ..models import Video
from ..models import Channel
from ..models import Discipline
from ..models import AdvancedNotes
from pod.authentication.models import AccessGroup

import re
import json
from http import HTTPStatus
from importlib import reload


class ChannelTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        self.c = Channel.objects.create(title="ChannelTest1")
        self.c2 = Channel.objects.create(title="ChannelTest2")
        self.theme = Theme.objects.create(title="Theme1", slug="blabla", channel=self.c)
        user = User.objects.create(username="pod", password="pod1234pod")
        self.v = Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.v.channel.add(self.c)
        self.v.save()

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        self.c.sites.add(site)
        self.c2.sites.add(site)

    @override_settings(ORGANIZE_BY_THEME=False)
    def test_get_channel_view(self):
        self.client = Client()
        response = self.client.get("/%s/" % self.c.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channel"], self.c)
        self.assertEqual(response.context["theme"], None)
        self.assertEqual(response.context["videos"].paginator.count, 1)
        print(
            "   --->  test_channel_without_theme" "_in_argument of ChannelTestView : OK !"
        )
        response = self.client.get("/%s/" % self.c2.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channel"], self.c2)
        self.assertEqual(response.context["theme"], None)
        self.assertEqual(response.context["videos"].paginator.count, 0)
        print(
            "   --->  test_channel_2_without_theme_in_argument"
            " of ChannelTestView : OK !"
        )
        response = self.client.get("/%s/%s/" % (self.c.slug, self.theme.slug))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        print("   --->  test_channel_with_theme_in_argument" " of ChannelTestView : OK !")

    def test_regroup_videos_by_theme(self):
        # Test get videos and theme from channel view
        self.client = Client()
        response = self.client.get("/%s/" % self.c.slug)
        expected = {
            "next_videos": None,
            "next": None,
            "previous": None,
            "parent_title": "",
            "title": self.c.title,
            "description": self.c.description,
            "headband": None,
            "theme_children": [{"slug": self.theme.slug, "title": self.theme.title}],
            "has_more_themes": False,
            "has_more_videos": False,
            "videos": [self.v],
            "count_themes": 1,
            "theme": None,
            "channel": self.c,
            "pages_info": "1/1",
            "organize_theme": True,
        }
        self.assertEqual(response.status_code, HTTPStatus.OK)
        for key in expected.keys():
            assert expected[key] == response.context[key]

        # Test ajax request, get videos and themes from channel view
        self.client = Client()
        response = self.client.get(
            "/%s/" % self.c.slug, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        expected["videos"] = [
            {
                "slug": self.v.slug,
                "title": self.v.title,
                "duration": self.v.duration_in_time,
                "thumbnail": self.v.get_thumbnail_card(),
                "is_video": self.v.is_video,
                "has_password": bool(self.v.password),
                "is_restricted": self.v.is_restricted,
                "has_chapter": self.v.chapter_set.all().count() > 0,
                "is_draft": self.v.is_draft,
            }
        ]
        expected.pop("organize_theme", None)
        expected.pop("theme", None)
        expected.pop("channel", None)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertCountEqual(expected, response.json())

        # Test ajax request, get only themes from channel view
        self.client = Client()
        response = self.client.get(
            "/%s/" % self.c.slug,
            {"target": "themes"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        expected.pop("next_videos", None)
        expected.pop("has_more_videos", None)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertCountEqual(expected, response.json())

        # Test ajax request, get only videos from channel view
        self.client = Client()
        response = self.client.get(
            "/%s/" % self.c.slug,
            {"target": "videos"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        expected["next_videos"] = None
        expected["has_more_videos"] = False

        expected.pop("next", None)
        expected.pop("previous", None)
        expected.pop("theme_children", None)
        expected.pop("has_more_themes", None)
        expected.pop("pages_info", None)
        expected.pop("count_themes", None)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertCountEqual(expected, response.json())


class MyChannelsTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        c1 = Channel.objects.create(title="ChannelTest1")
        c1.owners.add(user)
        c2 = Channel.objects.create(title="ChannelTest2")
        c2.owners.add(user)
        for c in Channel.objects.all():
            c.sites.add(site)

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of MyChannelsTestView : OK !")

    def test_get_mychannels_view(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/my_channels/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channels"].count(), 2)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/my_channels/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channels"].count(), 0)
        print(" --->  test_get_mychannels_view of MyChannelsTestView : OK !")


class ChannelEditTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        c1 = Channel.objects.create(title="ChannelTest1")
        c1.owners.add(user)
        c1.sites.add(site)

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()

        print(" --->  SetUp of ChannelEditTestView : OK !")

    def test_channel_edit_get_request(self):
        self.client = Client()
        channel = Channel.objects.get(title="ChannelTest1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/channel_edit/slugauhasard/")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/channel_edit/%s/" % channel.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["form"].instance, channel)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/channel_edit/%s/" % channel.slug)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_channel_edit_get_request" " of ChannelEditTestView : OK !")

    def test_channel_edit_post_request(self):
        self.client = Client()
        channel = Channel.objects.get(title="ChannelTest1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.post(
            "/channel_edit/%s/" % channel.slug,
            {"title": "ChannelTest1", "description": "<p>bl</p>\r\n"},
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(b"The changes have been saved." in response.content)
        c = Channel.objects.get(title="ChannelTest1")
        self.assertEqual(c.description, "<p>bl</p>")
        print("   --->  test_channel_edit_post_request" " of ChannelEditTestView : OK !")


class ThemeEditTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        c1 = Channel.objects.create(title="ChannelTest1")
        c1.owners.add(user)
        Theme.objects.create(
            title="Theme1",
            slug="theme1",
            channel=Channel.objects.get(title="ChannelTest1"),
        )
        Theme.objects.create(
            title="Theme2",
            slug="theme2",
            channel=Channel.objects.get(title="ChannelTest1"),
        )
        Theme.objects.create(
            title="Theme3",
            slug="theme3",
            channel=Channel.objects.get(title="ChannelTest1"),
        )
        c1.sites.add(site)

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        print(" --->  SetUp of ThemeEditTestView : OK !")

    def test_theme_edit_get_request(self):
        self.client = Client()
        channel = Channel.objects.get(title="ChannelTest1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/theme_edit/%s/" % channel.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channel"], channel)
        self.assertEqual(response.context["form_theme"].initial["channel"], channel)
        self.assertEqual(channel.themes.all().count(), 3)
        print(" --->  test_theme_edit_get_request of ThemeEditTestView : OK !")

    def test_theme_edit_post_request(self):
        self.client = Client()
        channel = Channel.objects.get(title="ChannelTest1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        # action new
        response = self.client.post(
            "/theme_edit/%s/" % channel.slug,
            {"action": "new"},
            follow=True,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channel"], channel)
        self.assertEqual(response.context["form_theme"].initial["channel"], channel)
        # action modify
        response = self.client.post(
            "/theme_edit/%s/" % channel.slug,
            {"action": "modify", "id": 1},
            follow=True,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channel"], channel)
        theme = Theme.objects.get(id=1)
        self.assertEqual(response.context["form_theme"].instance, theme)
        # action delete
        self.assertEqual(channel.themes.all().count(), 3)
        response = self.client.post(
            "/theme_edit/%s/" % channel.slug,
            {"action": "delete", "id": 1},
            follow=True,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channel"], channel)
        self.assertEqual(
            Channel.objects.get(title="ChannelTest1").themes.all().count(), 2
        )
        # action save
        # save new one
        response = self.client.post(
            "/theme_edit/%s/" % channel.slug,
            {
                "action": "save",
                "title": "Theme4",
                "channel": Channel.objects.get(title="ChannelTest1").id,
            },
            follow=True,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channel"], channel)
        theme = Theme.objects.get(title="Theme4")
        self.assertEqual(
            Channel.objects.get(title="ChannelTest1").themes.all().count(), 3
        )
        # save existing one
        response = self.client.post(
            "/theme_edit/%s/" % channel.slug,
            {
                "action": "save",
                "theme_id": 3,
                "title": "Theme3-1",
                "channel": Channel.objects.get(title="ChannelTest1").id,
            },
            follow=True,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["channel"], channel)
        theme = Theme.objects.get(id=3)
        self.assertEqual(theme.title, "Theme3-1")
        print(" --->  test_theme_edit_post_request of ThemeEditTestView : OK !")


class MyVideosTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test1.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        Video.objects.create(
            title="Video2",
            owner=user,
            video="test2.mp4",
            type=Type.objects.get(id=1),
        )
        Video.objects.create(
            title="Video3",
            owner=user,
            video="test3.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        Video.objects.create(
            title="Video4",
            owner=user2,
            video="test4.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

        for v in Video.objects.all():
            v.sites.add(site)

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()

        print(" --->  SetUp of MyChannelsTestView : OK !")

    def test_get_myvideos_view(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/my_videos/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 3)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/my_videos/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 1)
        print(" --->  test_get_myvideos_view of MyVideosTestView : OK !")


class VideosTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        # type, discipline, owner et tag
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        t1 = Type.objects.create(title="Type1")
        t2 = Type.objects.create(title="Type2")
        d1 = Discipline.objects.create(title="Discipline1")
        d2 = Discipline.objects.create(title="Discipline2")

        v = Video.objects.create(
            title="Video1",
            type=t1,
            tags="tag1 tag2",
            owner=user,
            video="test1.mp4",
            is_draft=False,
        )
        v.discipline.add(d1, d2)
        v = Video.objects.create(
            title="Video2",
            type=t2,
            tags="tag1 tag2",
            owner=user,
            video="test2.mp4",
        )
        v.discipline.add(d1, d2)
        v = Video.objects.create(
            title="Video3",
            type=t1,
            owner=user,
            video="test3.mp4",
            is_draft=False,
        )
        v = Video.objects.create(
            title="Video4",
            type=t2,
            tags="tag1",
            owner=user2,
            video="test4.mp4",
            is_draft=False,
        )
        v.discipline.add(d1)
        v = Video.objects.create(
            title="Video5",
            type=t1,
            tags="tag2",
            owner=user2,
            video="test4.mp4",
            is_draft=False,
        )
        v.discipline.add(d2)
        print(" --->  SetUp of VideosTestView : OK !")

    def test_get_videos_view(self):
        self.client = Client()
        response = self.client.get("/videos/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 4)
        # type
        response = self.client.get("/videos/?type=type1")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 3)
        response = self.client.get("/videos/?type=type2")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 1)
        response = self.client.get("/videos/?type=type2&type=type1")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 4)
        # discipline
        response = self.client.get("/videos/?discipline=discipline1")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 2)
        response = self.client.get("/videos/?discipline=discipline2")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 2)
        response = self.client.get(
            "/videos/?discipline=discipline1&discipline=discipline2"
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 3)
        # owner
        response = self.client.get("/videos/?owner=pod")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 2)
        response = self.client.get("/videos/?owner=pod2")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 2)
        response = self.client.get("/videos/?owner=pod&owner=pod2")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 4)
        # tag
        response = self.client.get("/videos/?tag=tag1")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 2)
        response = self.client.get("/videos/?tag=tag2")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 2)
        response = self.client.get("/videos/?tag=tag1&tag=tag2")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["videos"].paginator.count, 3)
        print(" --->  test_get_videos_view of VideosTestView : OK !")


class VideoTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        # type, discipline, owner et tag
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        user3 = User.objects.create(username="pod3", password="pod1234pod")
        AccessGroup.objects.create(code_name="group1", display_name="Group 1")
        AccessGroup.objects.create(code_name="group2", display_name="Group 2")
        AccessGroup.objects.create(code_name="group3", display_name="Group 3")
        v0 = Video.objects.create(
            title="Video1",
            owner=user,
            video="test1.mp4",
            type=Type.objects.get(id=1),
        )
        v = Video.objects.create(
            title="VideoWithAdditionalOwners",
            owner=user,
            video="test2.mp4",
            type=Type.objects.get(id=1),
            id=2,
        )
        v0.sites.add(site)
        v.sites.add(site)
        v.additional_owners.add(user2)

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()

        user3.owner.sites.add(Site.objects.get_current())
        user3.owner.save()

    def test_video_get_request(self):
        v = Video.objects.get(title="Video1")
        self.assertEqual(v.is_draft, True)
        # test draft
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, 302)
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, 403)
        # test normal
        self.client.logout()
        v.is_draft = False
        v.save()
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # test restricted
        v.is_restricted = True
        v.save()
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # test restricted group
        v.restrict_access_to_groups.add(AccessGroup.objects.get(code_name="group2"))
        v.restrict_access_to_groups.add(AccessGroup.objects.get(code_name="group3"))
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, 403)
        self.user.owner.accessgroup_set.add(AccessGroup.objects.get(code_name="group1"))
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, 403)
        self.user.owner.accessgroup_set.add(AccessGroup.objects.get(code_name="group2"))
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # TODO test with password
        v.is_restricted = False
        v.restrict_access_to_groups = []
        v.password = "password"
        v.save()
        self.client.logout()
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["form"])
        # TODO test with hashkey
        response = self.client.get("/video/%s/%s/" % (v.slug, v.get_hashkey()))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual("form" in response.context.keys(), False)
        v.is_draft = True
        v.save()
        response = self.client.get("/video/%s/%s/" % (v.slug, v.get_hashkey()))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual("form" in response.context.keys(), False)
        # Tests for additional owners
        v = Video.objects.get(title="VideoWithAdditionalOwners")
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.user = User.objects.get(username="pod3")
        self.client.force_login(self.user)
        response = self.client.get("/video/%s/" % v.slug)
        self.assertEqual(response.status_code, 403)


class VideoEditTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        user3 = User.objects.create(username="pod3", password="pod1234pod")
        video0 = Video.objects.create(
            title="Video1",
            owner=user,
            video="test1.mp4",
            type=Type.objects.get(id=1),
        )
        video = Video.objects.create(
            title="VideoWithAdditionalOwners",
            owner=user,
            video="test2.mp4",
            type=Type.objects.get(id=1),
        )
        video.save()
        video.sites.add(site)
        video0.sites.add(site)
        video.additional_owners.add(user2)

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()

        user3.owner.sites.add(Site.objects.get_current())
        user3.owner.save()

        print(" --->  SetUp of VideoEditTestView : OK !")

    def test_video_edit_get_request(self):
        self.client = Client()
        response = self.client.get("/video_edit/")
        self.assertEqual(response.status_code, 302)
        video = Video.objects.get(title="Video1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/video_edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.client.get("/video_edit/slugauhasard/")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/video_edit/%s/" % video.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["form"].instance, video)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/video_edit/%s/" % video.slug)
        self.assertEqual(response.status_code, 403)
        # Tests for additional owners
        video = Video.objects.get(title="VideoWithAdditionalOwners")
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/video_edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.client.get("/video_edit/%s/" % video.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["form"].instance, video)
        self.user = User.objects.get(username="pod3")
        self.client.force_login(self.user)
        response = self.client.get("/video_edit/%s/" % video.slug)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_video_edit_get_request" " of VideoEditTestView : OK !")

    def test_video_edit_post_request(self):
        self.client = Client()
        video = Video.objects.get(title="Video1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        # modify one
        response = self.client.post(
            "/video_edit/%s/" % video.slug,
            {
                "title": "VideoTest1",
                "description": "<p>bl</p>\r\n",
                "main_lang": "fr",
                "cursus": "0",
                "type": 1,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # print(response.context["form"].errors)
        self.assertTrue(b"The changes have been saved." in response.content)

        v = Video.objects.get(title="VideoTest1")
        self.assertEqual(v.description, "<p>bl</p>")
        videofile = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )
        response = self.client.post(
            "/video_edit/%s/" % v.slug,
            {
                "video": videofile,
                "title": "VideoTest1",
                "main_lang": "fr",
                "cursus": "0",
                "type": 1,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(b"The changes have been saved." in response.content)
        v = Video.objects.get(title="VideoTest1")
        p = re.compile(r"^videos/([\d\w]+)/file([_\d\w]*).mp4$")
        self.assertRegexpMatches(v.video.name, p)
        # new one
        videofile = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )
        self.client.post(
            "/video_edit/",
            {
                "video": videofile,
                "title": "VideoTest2",
                "description": "<p>coucou</p>\r\n",
                "main_lang": "fr",
                "cursus": "0",
                "type": 1,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(b"The changes have been saved." in response.content)
        v = Video.objects.get(title="VideoTest2")
        # Additional owners
        self.client = Client()
        video = Video.objects.get(title="VideoWithAdditionalOwners")
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        # modify one
        response = self.client.post(
            "/video_edit/%s/" % video.slug,
            {
                "title": "VideoTest3",
                "description": "<p>bl</p>\r\n",
                "main_lang": "fr",
                "cursus": "0",
                "type": 1,
                "additional_owners": [self.user.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(b"The changes have been saved." in response.content)
        v = Video.objects.get(title="VideoTest3")
        self.assertEqual(v.description, "<p>bl</p>")
        videofile = SimpleUploadedFile(
            "file.mp4", b"file_content", content_type="video/mp4"
        )
        response = self.client.post(
            "/video_edit/%s/" % v.slug,
            {
                "video": videofile,
                "title": "VideoTest3",
                "main_lang": "fr",
                "cursus": "0",
                "type": 1,
                "additional_owners": [self.user.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(b"The changes have been saved." in response.content)
        print("   --->  test_video_edit_post_request" " of VideoEditTestView : OK !")


class video_deleteTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        video0 = Video.objects.create(
            title="Video1",
            owner=user,
            video="test1.mp4",
            type=Type.objects.get(id=1),
        )
        video = Video.objects.create(
            title="VideoWithAdditionalOwners",
            owner=user,
            video="test2.mp4",
            type=Type.objects.get(id=1),
            id=2,
        )

        video0.sites.add(site)
        video.sites.add(site)
        video.additional_owners.add(user2)

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of video_deleteTestView : OK !")

    def test_video_delete_get_request(self):
        self.client = Client()
        video = Video.objects.get(title="Video1")
        response = self.client.get("/video_delete/%s/" % video.slug)
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/video_delete/slugauhasard/")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/video_delete/%s/" % video.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/video_delete/%s/" % video.slug)
        self.assertEqual(response.status_code, 403)
        # An additional owner can't delete the video
        video = Video.objects.get(title="VideoWithAdditionalOwners")
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/video_delete/%s/" % video.slug)
        self.assertEqual(response.status_code, 403)
        self.user = User.objects.get(username="pod")
        print(" --->  test_video_edit_get_request" " of video_deleteTestView : OK !")

    def test_video_delete_post_request(self):
        self.client = Client()
        video = Video.objects.get(title="Video1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.post(
            "/video_delete/%s/" % video.slug,
            {
                "agree": True,
            },
        )
        self.assertRedirects(response, "/my_videos/")
        self.assertEqual(Video.objects.all().count(), 1)
        video = Video.objects.get(title="VideoWithAdditionalOwners")
        response = self.client.post(
            "/video_delete/%s/" % video.slug,
            {
                "agree": True,
            },
        )
        self.assertRedirects(response, "/my_videos/")
        self.assertEqual(Video.objects.all().count(), 0)
        print(" --->  test_video_edit_post_request" " of video_deleteTestView : OK !")


class video_notesTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        v = Video.objects.create(
            title="Video1",
            owner=user,
            video="test1.mp4",
            type=Type.objects.get(id=1),
        )
        v.sites.add(site)

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        print(" --->  SetUp of video_notesTestView : OK !")

    def test_video_notesTestView_get_request(self):
        self.client = Client()
        video = Video.objects.get(title="Video1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/video/%s/" % video.slug)
        """
        note = Notes.objects.get(
            user=User.objects.get(username="pod"),
            video=video)
        """
        self.client.logout()
        response = self.client.get("/video_notes/%s/" % video.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.client.force_login(self.user)
        response = self.client.get("/video_notes/%s/" % video.slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # self.assertEqual(response.context['notesForm'].instance, note)
        print(
            " --->  test_video_notesTestView_get_request" " of video_notesTestView : OK !"
        )

    def test_video_notesTestView_post_request(self):
        self.client = Client()
        video = Video.objects.get(title="Video1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        note = AdvancedNotes.objects.create(
            user=User.objects.get(username="pod"), video=video
        )
        self.assertEqual(note.note, None)
        self.assertEqual(note.timestamp, None)
        self.assertEqual(note.status, "0")
        response = self.client.post(
            "/video_notes/%s/" % video.slug,
            {
                "action": "save_note",
                "note": "coucou",
                "timestamp": 10,
                "status": "0",
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(b"The note has been saved." in response.content)
        note = AdvancedNotes.objects.get(
            user=User.objects.get(id=self.user.id),
            video=video,
            timestamp=10,
            status="0",
        )
        self.assertEqual(note.note, "coucou")
        self.assertEqual(note.timestamp, 10)
        self.assertEqual(note.status, "0")
        print(
            " --->  test_video_notesTestView_post_request"
            " of video_notesTestView : OK !"
        )


class video_countTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test1.mp4",
            type=Type.objects.get(id=1),
        )
        print(" --->  SetUp of video_countTestView : OK !")

    def test_video_countTestView_get_request(self):
        self.client = Client()
        video = Video.objects.get(title="Video1")
        response = self.client.get("/video_count/2/")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/video_count/%s/" % video.id)
        self.assertEqual(response.status_code, 403)
        print(
            " --->  test_video_countTestView_get_request" " of video_countTestView : OK !"
        )

    def test_video_countTestView_post_request(self):
        self.client = Client()
        video = Video.objects.get(title="Video1")
        print("count : %s" % video.get_viewcount())
        self.assertEqual(video.get_viewcount(), 0)
        response = self.client.post("/video_count/%s/" % video.id, {})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(b"ok" in response.content)
        self.assertEqual(video.get_viewcount(), 1)
        print(
            " --->  test_video_countTestView_post_request"
            " of video_countTestView : OK !"
        )


# add test to video record : USE_VIDEO_RECORD = True
class video_recordTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        User.objects.create(username="pod", password="pod1234pod")
        print(" --->  SetUp of video_recordTestView : OK !")

    def test_video_recordTestView_get_request(self):
        self.client = Client()
        response = self.client.get("/video_record/")
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/video_record/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

        print(
            " --->  test_video_recordTestView_get_request"
            " of video_recordTestView : OK !"
        )

    @override_settings(DEBUG=True, RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=True)
    def test_video_recordTestView_get_request_restrict(self):
        reload(views)
        self.client = Client()
        response = self.client.get("/video_record/")
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/video_record/")
        self.assertEquals(response.context["access_not_allowed"], True)
        self.user.is_staff = True
        self.user.save()
        response = self.client.get("/video_record/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        print(
            " --->  test_video_recordTestView_get_request_restrict"
            " of video_recordTestView : OK !"
        )

    def test_video_recordTestView_upload_recordvideo(self):
        reload(views)
        video = SimpleUploadedFile("file.mp4", b"file_content", content_type="video/mp4")
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("video_record"),
            {"video": video, "title": "test upload"},
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context, None)
        try:
            data = json.loads(response.content)
        except (RuntimeError, TypeError, NameError, AttributeError) as err:
            print("Unexpected error: {0}".format(err))
            data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["url_edit"], "/video_edit/0001-test-upload/")
        self.assertEqual(Video.objects.all().count(), 1)
        vid = Video.objects.get(id=1)
        self.assertEqual(vid.title, "test upload")
        print(
            " --->  test_video_recordTestView_upload_recordvideo"
            " of video_recordTestView : OK !"
        )


class VideoTestUpdateOwner(TransactionTestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        self.client = Client()

        self.admin = User.objects.create(
            first_name="pod",
            last_name="Admin",
            username="admin",
            password="admin1234admin",
            is_superuser=True,
        )
        self.simple_user = User.objects.create(
            first_name="Pod", last_name="User", username="pod", password="pod1234pod"
        )
        self.v1 = Video.objects.create(
            title="Video1",
            owner=self.admin,
            video="test1.mp4",
            type=Type.objects.get(id=1),
        )
        self.v2 = Video.objects.create(
            title="Video2",
            owner=self.admin,
            video="test3.mp4",
            type=Type.objects.get(id=1),
        )
        print(" --->  SetUp of VideoTestUpdateOwner : OK !")

    def test_update_video_owner(self):
        url = reverse("update_video_owner", kwargs={"user_id": self.admin.id})

        # Authentication required move TEMPORARY_REDIRECT
        response = self.client.post(
            url,
            json.dumps({"videos": [1, 2], "owner": [self.simple_user.id]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # Access Denied: user is not admin
        self.client.force_login(self.simple_user)
        access_url = reverse("admin:video_updateowner_changelist")
        response = self.client.get(access_url, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Method not allowed
        self.client.force_login(self.admin)
        url = reverse("update_video_owner", kwargs={"user_id": self.admin.id})
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        expected = {
            "success": False,
            "detail": "Method not allowed: Please use post method",
        }
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)

        # Partial update request
        response = self.client.post(
            url,
            json.dumps(
                {
                    # video with id 100 doesn't exist
                    "videos": [1, 2, 100],
                    "owner": self.simple_user.id,
                }
            ),
            content_type="application/json",
        )
        expected = {"success": True, "detail": "One or more videos not updated"}
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)

        # Good request
        response = self.client.post(
            url,
            json.dumps({"videos": [1, 2], "owner": self.simple_user.id}),
            content_type="application/json",
        )

        expected = {"success": True, "detail": "Update successfully"}
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)
        self.assertEqual(Video.objects.filter(owner=self.simple_user).count(), 2)

    def tearDown(self):
        super(VideoTestUpdateOwner, self).tearDown()


class VideoTestFiltersViews(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        self.client = Client()

        self.admin = User.objects.create(
            first_name="pod",
            last_name="Admin",
            username="admin",
            password="admin1234admin",
            is_superuser=True,
        )
        self.simple_user = User.objects.create(
            first_name="Pod", last_name="User", username="pod", password="pod1234pod"
        )
        self.v1 = Video.objects.create(
            title="Video1",
            owner=self.admin,
            video="test1.mp4",
            type=Type.objects.get(id=1),
        )
        self.v2 = Video.objects.create(
            title="Video2",
            owner=self.admin,
            video="test3.mp4",
            type=Type.objects.get(id=1),
        )
        print(" --->  SetUp of VideoTestFiltersViews : OK !")

    def test_filter_owners(self):
        url = reverse("filter_owners")

        # Authentication required
        response = self.client.get(url, {"q": "pod"})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # authenticated
        self.client.force_login(self.admin)
        response = self.client.get(url, {"q": "pod user"})
        expected = [
            {
                "id": self.simple_user.id,
                "first_name": self.simple_user.first_name,
                "last_name": self.simple_user.last_name,
            },
        ]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)
        response = self.client.get(url, {"q": "user pod"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)

        response = self.client.get(url, {"q": "admin pod"})
        expected = [
            {
                "id": self.admin.id,
                "first_name": self.admin.first_name,
                "last_name": self.admin.last_name,
            },
        ]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)
        response = self.client.get(url, {"q": "pod admin"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)

        response = self.client.get(url, {"q": "pod"})
        expected = [
            *expected,
            {
                "id": self.simple_user.id,
                "first_name": self.simple_user.first_name,
                "last_name": self.simple_user.last_name,
            },
        ]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)

        expected = []
        response = self.client.get(url, {"q": "user not exists"})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)

    def test_filter_videos(self):
        url = reverse("filter_videos", kwargs={"user_id": self.admin.id})

        # Authentication required
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # authenticated
        self.client.force_login(self.admin)
        response = self.client.get(url)
        expected = {
            "count": 2,
            "next": None,
            "previous": None,
            "page_infos": "1/1",
            "results": [
                {
                    "id": self.v1.id,
                    "title": self.v1.title,
                    "thumbnail": self.v1.get_thumbnail_url(),
                },
                {
                    "id": self.v2.id,
                    "title": self.v2.title,
                    "thumbnail": self.v2.get_thumbnail_url(),
                },
            ],
        }
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)

        response = self.client.get(url, {"q": self.v1.title})
        expected = {
            **expected,
            "count": 1,
            "results": [
                {
                    "id": self.v1.id,
                    "title": self.v1.title,
                    "thumbnail": self.v1.get_thumbnail_url(),
                },
            ],
        }
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(json.loads(response.content.decode("utf-8")), expected)

    def tearDown(self):
        super(VideoTestFiltersViews, self).tearDown()
