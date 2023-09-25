from unittest import skipUnless
from django.http import JsonResponse
from datetime import date
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from pod.authentication.models import User
from pod.video.models import Channel, Theme, Video, Type
from pod.video.views import get_all_views_count, stats_view
from django.contrib.sites.models import Site
from pod.authentication.models import AccessGroup
# from django.contrib.auth.hashers import make_password

from pod.video_encode_transcript.models import EncodingVideo
from pod.video_encode_transcript.models import VideoRendition

import json
import logging

TODAY = date.today()
USE_STATS_VIEW = getattr(settings, "USE_STATS_VIEW", False)


class TestStatsView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        self.logger = logging.getLogger("django.request")
        # self.previous_level = self.logger.getEffectiveLevel()
        # Remove warning log
        self.logger.setLevel(logging.ERROR)

        self.client = Client()
        self.channel = Channel.objects.create(title="statsChannelTest", visible=True)
        self.theme = Theme.objects.create(title="statsThemeTest", channel=self.channel)
        self.t1 = Type.objects.get(id=1)
        self.user = User.objects.create(
            username="doejohn",
            first_name="John",
            last_name="DOE",
            password="Toto1234_4321",
        )
        self.visitor = User.objects.create(
            username="visitorpod",
            first_name="Visitor",
            last_name="Pod",
            password="Visitor1234*",
        )
        self.superuser = User.objects.create(
            username="SuperUser",
            first_name="Super",
            last_name="User",
            password="SuperPassword1234",
            is_superuser=True,
        )
        self.video = Video.objects.create(
            title="Test stats view",
            is_draft=False,
            encoding_in_progress=False,
            owner=self.user,
            video="teststatsviews.mp4",
            type=self.t1,
        )
        self.video2 = Video.objects.create(
            title="Test stats view second",
            owner=self.user,
            is_draft=False,
            encoding_in_progress=False,
            video="teststatsviewssecond.mp4",
            type=self.t1,
        )
        self.video3 = Video.objects.create(
            title="Test stats view third",
            owner=self.user,
            is_draft=False,
            encoding_in_progress=False,
            video="teststatsviewthird.mp4",
            type=self.t1,
        )
        # add encoding to video
        EncodingVideo.objects.create(
            video=self.video,
            encoding_format="video/mp4",
            rendition=VideoRendition.objects.get(id=1),
        )
        EncodingVideo.objects.create(
            video=self.video2,
            encoding_format="video/mp4",
            rendition=VideoRendition.objects.get(id=1),
        )
        EncodingVideo.objects.create(
            video=self.video3,
            encoding_format="video/mp4",
            rendition=VideoRendition.objects.get(id=1),
        )
        self.video.channel.set([self.channel])
        self.video.theme.set([self.theme])
        self.video2.channel.set([self.channel])
        self.video2.theme.set([self.theme])
        self.url_stats_exists = True

        self.user.owner.sites.add(Site.objects.get_current())
        self.user.owner.save()

        self.visitor.owner.sites.add(Site.objects.get_current())
        self.visitor.owner.save()

        self.superuser.owner.sites.add(Site.objects.get_current())
        self.superuser.owner.save()
        try:
            self.stat_video_url = (
                reverse("video:video_stats_view", kwargs={"slug": self.video.slug})
                + "?from=video"
            )
            self.stat_channel_url = (
                reverse("video:video_stats_view", kwargs={"slug": self.channel.slug})
                + "?from=channel"
            )
            self.stat_theme_url = (
                reverse(
                    "video:video_stats_view",
                    kwargs={
                        "slug": self.channel.slug,
                        "slug_t": self.theme.slug,
                    },
                )
                + "?from=theme"
            )
            USE_STATS_VIEW = True
        except NoReverseMatch:
            USE_STATS_VIEW = False
            print("Statistics URL defined =======> : " + USE_STATS_VIEW)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_stats_view_GET_request_video(self):
        response = self.client.get(self.stat_video_url)
        # Check that the view function is stats_view
        self.assertEqual(response.resolver_match.func, stats_view)
        # Check that the response is 200 OK.
        # and content the expected title
        self.assertContains(
            response,
            (
                b"Video viewing statistics for %s"
                % self.video.title.capitalize().encode("utf-8")
            ),
            status_code=200,
        )
        # Check that the response is 404 Not Found.
        # Check the response contains the error message
        stat_video_url = (
            reverse("video:video_stats_view", kwargs={"slug": "0001_videodoesnotexist"})
            + "?from=video"
        )
        response = self.client.get(stat_video_url)
        self.assertEqual(response.status_code, 404)
        """
        self.assertContains(
                response,
                b"The following video does not exist : \
                        0001_videodoesnotexist",
                status_code=404)
        """

    @skipUnless(USE_STATS_VIEW, "Require activate URL video_stats_view")
    def test_stats_view_GET_request_videos(self):
        stat_url_videos = reverse("video:video_stats_view")
        response = self.client.get(stat_url_videos, {"from": "videos"})
        self.assertContains(response, b"Pod video viewing statistics", status_code=200)

    @skipUnless(USE_STATS_VIEW, "Require acitvate URL video_stats_view")
    def test_stats_view_GET_request_channel(self):
        # print("ABCDE " + self.stat_channel_url)
        response = self.client.get(self.stat_channel_url)
        # Check that the view function is stats_view
        self.assertEqual(response.resolver_match.func, stats_view)
        # Check that the response is 200 OK.
        # Check that the response contains the expected title
        self.assertContains(
            response,
            (
                b"Video viewing statistics for the channel %s"
                % self.channel.slug.encode("utf-8")
            ),
            status_code=200,
        )
        # Check that the response is 404 Not Found.
        # Check that the response contains the error message
        stat_channel_url = (
            reverse("video:video_stats_view", kwargs={"slug": "0001_channeldoesnotexist"})
            + "?from=channel"
        )
        response = self.client.get(stat_channel_url)
        msg = b"The following channel does not exist or contain any videos: %b"
        self.assertContains(response, msg % b"0001_channeldoesnotexist", status_code=404)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_stats_view_GET_request_theme(self):
        response = self.client.get(self.stat_theme_url)
        # Check that the view function is stats_view
        self.assertEqual(response.resolver_match.func, stats_view)
        # Check that the response is 200 OK.
        # Check that the response contains the expected title
        self.assertContains(
            response,
            (
                b"Video viewing statistics for the theme %s"
                % self.theme.slug.encode("utf-8")
            ),
            status_code=200,
        )
        # Check that the response is 404 Not Found.
        # Check that the response contains the error message
        stat_theme_url = (
            reverse(
                "video:video_stats_view",
                kwargs={
                    "slug": "0001_channeldoesnotexist",
                    "slug_t": "0001_themedoesnotexist",
                },
            )
            + "?from=theme"
        )
        response = self.client.get(stat_theme_url)
        msg = b"The following theme does not exist or contain any videos: %b"
        self.assertContains(response, msg % b"0001_themedoesnotexist", status_code=404)

    @skipUnless(USE_STATS_VIEW, "Require activate URL video_stats_view")
    def test_stats_view_POST_request_video(self):
        data = [
            {
                "title": self.video.title,
                "slug": self.video.slug,
                **get_all_views_count(self.video.id),
            },
            {"min_date": TODAY},
        ]
        expected_content = JsonResponse(data, safe=False).content
        response = self.client.post(self.stat_video_url)
        # Check that the view function is stats_view
        self.assertEqual(response.resolver_match.func, stats_view)
        # Check that the response is 200 OK and
        self.assertEqual(response.status_code, 200)
        # the content contains the title of the video and expected data
        self.assertEqual(response.content, expected_content)

    @skipUnless(USE_STATS_VIEW, "Require activate URL video_stats_view")
    def test_stats_view_POST_request_videos(self):
        stat_url_videos = reverse("video:video_stats_view")
        response = self.client.post(stat_url_videos)
        # Check that the view function is stats_view
        self.assertEqual(response.resolver_match.func, stats_view)
        # Check that the response is 200 OK and
        self.assertEqual(response.status_code, 200)
        videos_expected = [self.video, self.video2, self.video3]
        for video in videos_expected:
            data = {
                "title": self.video.title,
                "slug": self.video.slug,
                **get_all_views_count(video.id),
            }
            # the content contains the title of the video and expected data
            self.assertIn(json.dumps(data), response.content.decode("utf-8"))
        # the content contains the title of the video and expected data
        self.assertContains(
            response, json.dumps({"min_date": TODAY.strftime("%Y-%m-%d")})
        )

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_stats_view_POST_request_channel(self):
        response = self.client.post(self.stat_channel_url)
        # Check that the view function is stats_view
        self.assertEqual(response.resolver_match.func, stats_view)
        # Check that the response is 200 OK and
        self.assertEqual(response.status_code, 200)
        videos_expected = [self.video, self.video2]
        for video in videos_expected:
            data = {
                "title": video.title,
                "slug": video.slug,
                **get_all_views_count(video.id),
            }
            # the content contains the expected data
            self.assertIn(json.dumps(data), response.content.decode("utf-8"))
        # the content contains the expected data
        self.assertContains(
            response, json.dumps({"min_date": TODAY.strftime("%Y-%m-%d")})
        )

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_stats_view_POST_request_theme(self):
        response = self.client.post(self.stat_theme_url)
        # Check that the view function is stats_view
        self.assertEqual(response.resolver_match.func, stats_view)
        # Check that the response is 200 OK and
        self.assertEqual(response.status_code, 200)
        videos_expected = [self.video, self.video2]
        for video in videos_expected:
            data = {
                "title": video.title,
                "slug": video.slug,
                **get_all_views_count(video.id),
            }
            # the content contains the expected data
            self.assertIn(json.dumps(data), response.content.decode("utf-8"))
        # the content contains the expected data
        self.assertContains(
            response, json.dumps({"min_date": TODAY.strftime("%Y-%m-%d")})
        )

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_stats_view_GET_request_video_access_rights(self):
        """Test video restrictions (by password, by group, or private video)."""
        # *********** Test restricted by password ************ #
        password = "ThisVideoRequireAPassword"
        self.video3.password = password  # make_password(password, hasher="pbkdf2_sha256")
        self.video3.save()
        url = reverse("video:video_stats_view", kwargs={"slug": self.video3.slug})
        response = self.client.get(url, {"from": "video"})
        input_expected = '<input type="password" name="password" \
                placeholder="Password" id="id_password" class="required form-control" \
                required>'
        # Test that the response is 200 Ok
        self.assertEqual(response.status_code, 200)
        # Test thant the response content contains "password input"
        self.assertInHTML(input_expected, response.content.decode("utf-8"))

        # Test with passing a good video password
        response = self.client.post(url + "?from=video", {"password": password})
        title_expected = (
            '<h1 class="page_title h2">Video viewing statistics for %s</h1>'
        ) % self.video3.title.capitalize()
        # Test that the response is 200 OK.
        # Test that the response content contains the expected title
        self.assertContains(response, title_expected.encode(), status_code=200)

        # Test with the owner of the video who doesn't need to
        # specify a password
        self.client.force_login(self.user)
        response = self.client.get(url, {"from": "video"})
        self.assertContains(response, title_expected.encode(), status_code=200)

        # Test with the superuser who doesn't need to
        # specify a password
        self.client.logout()
        self.client.force_login(self.superuser)
        response = self.client.get(url, {"from": "video"})
        self.assertContains(response, title_expected.encode(), status_code=200)

        # ************ Test restricted by group ************** #
        group1 = AccessGroup.objects.create(code_name="group1")
        self.video3.password = None
        self.video3.is_restricted = True
        self.video3.restrict_access_to_groups.add(group1)
        self.video3.save()
        # login the visitor
        self.client.logout()
        self.client.force_login(self.visitor)
        response = self.client.get(url, {"from": "video"})
        # Test that connected visitor do not has access to
        # the video that is restricted by group which visitor
        # do not has access rights
        self.assertContains(
            response,
            "You do not have access rights to this video: %s" % self.video3.slug,
            status_code=404,
        )
        # add visitor to the group of the video
        # test that visitor has access rights
        self.visitor.owner.accessgroup_set.add(group1)
        response = self.client.get(url, {"from": "video"})
        self.assertContains(response, title_expected.encode(), status_code=200)

        # Disconnect visitor and connect the owner of the video
        self.client.logout()
        self.client.force_login(self.user)
        response = self.client.get(url, {"from": "video"})
        # Test that owner has access rights to the video
        self.assertContains(response, title_expected.encode(), status_code=200)
        # Test if that superuser has access rights
        self.client.logout()
        self.client.force_login(self.superuser)
        response = self.client.get(url, {"from": "video"})
        self.assertContains(response, title_expected.encode(), status_code=200)

        # *************** Test private video ****************** #
        self.video3.is_draft = True
        self.video3.is_restricted = False
        self.video3.restrict_access_to_groups.remove(group1)
        self.video3.save()
        self.client.logout()
        # Test that connected visitor doesn't have access rights
        self.client.force_login(self.visitor)
        response = self.client.get(url, {"from": "video"})
        self.assertContains(
            response,
            "You do not have access rights to this video: %s" % self.video3.slug,
            status_code=404,
        )
        self.client.logout()
        # Test that connected owner has access rights
        self.client.force_login(self.user)
        response = self.client.get(url, {"from": "video"})
        self.assertContains(response, title_expected.encode("utf-8"), status_code=200)

        # Test that connected superuser has access rights
        self.client.logout()
        self.client.force_login(self.superuser)
        response = self.client.get(url, {"from": "video"})
        self.assertContains(response, title_expected.encode("utf-8"), status_code=200)
        del title_expected
        del response
        del password

    def tearDown(self):
        del self.video
        del self.video2
        del self.video3
        del self.stat_video_url
        del self.stat_channel_url
        del self.stat_theme_url
        del self.channel
        del self.theme
        del self.visitor
        del self.user
        del self.superuser
        del self.client
        del self.t1
