"""Esup-Pod Stats view test cases.

*  run with 'python manage.py test pod.video.tests.test_stats_view'
"""

import json
import logging
from datetime import date, timedelta
from unittest import skipUnless
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.http import JsonResponse
from django.test import Client, RequestFactory, TestCase
from django.urls import NoReverseMatch, reverse

from pod.authentication.models import AccessGroup, User
from pod.video.models import Channel, Theme, Type, Video, ViewCount
from pod.video.views import get_all_views_count, stats_view
from pod.video_encode_transcript.models import EncodingVideo, VideoRendition

# from django.contrib.auth.hashers import make_password


TODAY = date.today()
USE_STATS_VIEW = getattr(settings, "USE_STATS_VIEW", False)


class TestStatsView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
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
            print("Statistics URL defined =======>: %s" % USE_STATS_VIEW)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_stats_view_GET_request_video(self) -> None:
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
                b"The following video does not exist: \
                        0001_videodoesnotexist",
                status_code=404)
        """

    def test_missing_video_slug_is_escaped(self) -> None:
        """The reflected missing-video message must not render slug markup."""
        malicious_slug = '<img src=x onerror="alert(1)">'
        request = RequestFactory().get("/video-stats/?from=video")
        request.user = self.superuser

        with patch("pod.video.views.get_videos", return_value=([], "")):
            response = stats_view(request, slug=malicious_slug)

        content = response.content.decode()
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("<img", content)
        self.assertIn("&lt;img", content)

    @skipUnless(USE_STATS_VIEW, "Require activate URL video_stats_view")
    def test_stats_view_GET_request_videos(self) -> None:
        stat_url_videos = reverse("video:video_stats_view")
        response = self.client.get(stat_url_videos, {"from": "videos"})
        self.assertContains(response, b"Pod video viewing statistics", status_code=200)

    @skipUnless(USE_STATS_VIEW, "Require activate URL video_stats_view")
    def test_stats_view_GET_request_channel(self) -> None:
        response = self.client.get(self.stat_channel_url)
        # Check that the view function is stats_view
        self.assertEqual(response.resolver_match.func, stats_view)
        # Check that the response is 200 OK and contains the expected title
        self.assertContains(
            response,
            (
                b"Video viewing statistics for the channel %s"
                % self.channel.slug.encode("utf-8")
            ),
            status_code=200,
        )
        slug = "0001_channeldoesnotexist"
        # Check that the response is 404 Not Found and contains the error message
        stat_channel_url = (
            reverse("video:video_stats_view", kwargs={"slug": slug}) + "?from=channel"
        )
        response = self.client.get(stat_channel_url)
        msg = (
            "The following “channel” type target does not exist or contains no videos: %s"
            % slug
        )
        self.assertContains(response, msg, status_code=404)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_stats_view_GET_request_theme(self) -> None:
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

        slug_t = "0001_themedoesnotexist"
        # Check that the response is 404 Not Found.
        # Check that the response contains the error message
        stat_theme_url = (
            reverse(
                "video:video_stats_view",
                kwargs={
                    "slug": "0001_channeldoesnotexist",
                    "slug_t": slug_t,
                },
            )
            + "?from=theme"
        )
        response = self.client.get(stat_theme_url)
        msg = (
            "The following “theme” type target does not exist or contains no videos: %s"
            % slug_t
        )
        self.assertContains(response, msg, status_code=404)

    @skipUnless(USE_STATS_VIEW, "Require activate URL video_stats_view")
    def test_stats_view_POST_request_video(self) -> None:
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
    def test_stats_view_POST_request_videos(self) -> None:
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
    def test_stats_view_POST_request_channel(self) -> None:
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
    def test_stats_view_POST_request_theme(self) -> None:
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
    def test_stats_view_GET_request_video_access_rights(self) -> None:
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

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    @patch("pod.video.views.VIEW_STATS_AUTH", True)
    def test_login_requirement_does_not_replace_video_authorization(self) -> None:
        """Requiring login must still enforce the video password afterwards."""
        self.video.password = "StatsPassword"
        self.video.save()
        for url in (self.stat_video_url, reverse("video:video_stats_view")):
            for method in ("get", "post"):
                with self.subTest(url=url, method=method):
                    response = getattr(self.client, method)(url)
                    self.assertEqual(response.status_code, 302)

        self.client.force_login(self.visitor)
        self.assertContains(self.client.get(self.stat_video_url), 'name="password"')
        self.assertEqual(self.client.post(self.stat_video_url).status_code, 403)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_password_post_requires_authorization_with_valid_csrf(self) -> None:
        """A valid CSRF token alone must never expose protected statistics."""
        self.video.password = "StatsPassword"
        self.video.save()

        for user in (None, self.visitor):
            client = Client(enforce_csrf_checks=True)
            if user is not None:
                client.force_login(user)
            response = client.get(self.stat_video_url)
            self.assertContains(response, 'name="password"')
            csrf_token = client.cookies[settings.CSRF_COOKIE_NAME].value
            for password_data in ({}, {"password": "wrong-password"}):
                with self.subTest(user=user, password=password_data):
                    response = client.post(
                        self.stat_video_url,
                        {"csrfmiddlewaretoken": csrf_token, **password_data},
                    )
                    self.assertEqual(response.status_code, 403)
                    self.assertNotIn(b'"since_created":', response.content)

            response = client.post(
                self.stat_video_url,
                {"csrfmiddlewaretoken": csrf_token, "password": self.video.password},
            )
            self.assertContains(response, self.video.title.capitalize())
            response = client.post(
                self.stat_video_url, {"csrfmiddlewaretoken": csrf_token}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()[0]["slug"], self.video.slug)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_password_authorization_survives_ajax_and_period_changes(self) -> None:
        """Unlocking the page also authorizes its following statistics requests."""
        self.video.password = "StatsPassword"
        self.video.save()
        previous_day = TODAY - timedelta(days=1)
        ViewCount.objects.create(video=self.video, date=previous_day, count=7)
        ViewCount.objects.create(video=self.video, date=TODAY, count=3)

        response = self.client.post(
            self.stat_video_url, {"password": self.video.password}
        )
        self.assertContains(response, self.video.title.capitalize())
        self.assertNotContains(response, 'name="password"')
        response = self.client.get(self.stat_video_url)
        self.assertNotContains(response, 'name="password"')
        for period, expected_count in ((previous_day, 7), (TODAY, 3)):
            with self.subTest(period=period):
                response = self.client.post(
                    self.stat_video_url, {"periode": period.isoformat()}
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()[0]["day"], expected_count)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_password_authorization_is_limited_to_video_and_session(self) -> None:
        """Unlocking one video does not unlock another video or another client."""
        for video in (self.video, self.video2):
            video.password = "SamePassword"
            video.save()
        response = self.client.post(
            self.stat_video_url, {"password": self.video.password}
        )
        self.assertEqual(response.status_code, 200)

        other_url = (
            reverse("video:video_stats_view", kwargs={"slug": self.video2.slug})
            + "?from=video"
        )
        self.assertEqual(self.client.post(other_url).status_code, 403)
        self.assertEqual(Client().post(self.stat_video_url).status_code, 403)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_password_change_invalidates_existing_authorization(self) -> None:
        """A previous password grant must expire when the video password changes."""
        self.video.password = "PreviousPassword"
        self.video.save()
        self.assertEqual(
            self.client.post(
                self.stat_video_url, {"password": self.video.password}
            ).status_code,
            200,
        )
        self.video.password = "ReplacementPassword"
        self.video.save()

        self.assertEqual(self.client.post(self.stat_video_url).status_code, 403)
        self.assertContains(self.client.get(self.stat_video_url), 'name="password"')
        self.assertEqual(
            self.client.post(
                self.stat_video_url, {"password": self.video.password}
            ).status_code,
            200,
        )
        self.assertEqual(self.client.post(self.stat_video_url).status_code, 200)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_restrictions_apply_to_get_and_post(self) -> None:
        """A password submission must not bypass draft or group restrictions."""
        group = AccessGroup.objects.create(code_name="stats-restricted")
        self.client.force_login(self.visitor)
        for restriction in ("draft", "group"):
            self.video.is_draft = restriction == "draft"
            self.video.is_restricted = restriction == "group"
            self.video.restrict_access_to_groups.clear()
            if restriction == "group":
                self.video.restrict_access_to_groups.add(group)
            for password in (None, "StatsPassword"):
                self.video.password = password
                self.video.save()
                for method, data in (
                    ("get", {}),
                    ("post", {}),
                    ("post", {"password": password or ""}),
                ):
                    with self.subTest(
                        restriction=restriction, password=password, method=method
                    ):
                        response = getattr(self.client, method)(self.stat_video_url, data)
                        self.assertIn(response.status_code, (403, 404))
                        self.assertNotIn(b'"since_created":', response.content)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_group_membership_is_rechecked_after_password_authorization(self) -> None:
        """A session grant must not preserve access after group membership removal."""
        group = AccessGroup.objects.create(code_name="stats-members")
        self.video.password = "StatsPassword"
        self.video.is_restricted = True
        self.video.save()
        self.video.restrict_access_to_groups.add(group)
        self.visitor.owner.accessgroup_set.add(group)
        self.client.force_login(self.visitor)
        self.assertContains(self.client.get(self.stat_video_url), 'name="password"')
        self.assertEqual(self.client.post(self.stat_video_url).status_code, 403)
        self.assertEqual(
            self.client.post(
                self.stat_video_url, {"password": self.video.password}
            ).status_code,
            200,
        )
        self.assertEqual(self.client.post(self.stat_video_url).status_code, 200)

        self.visitor.owner.accessgroup_set.remove(group)
        for method in ("get", "post"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.stat_video_url)
                self.assertIn(response.status_code, (403, 404))

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_privileged_users_keep_access_without_password(self) -> None:
        """Owners, co-owners, superusers and statistics managers retain access."""
        manager = User.objects.create(username="stats-manager")
        manager.owner.sites.add(Site.objects.get_current())
        manager.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="video", codename="change_viewcount"
            )
        )
        self.video.additional_owners.add(self.visitor)
        self.video.password = "StatsPassword"
        self.video.is_draft = True
        self.video.is_restricted = True
        self.video.save()
        self.video.restrict_access_to_groups.add(
            AccessGroup.objects.create(code_name="stats-privileged")
        )

        for user in (self.user, self.visitor, self.superuser, manager):
            self.client.force_login(user)
            with self.subTest(user=user):
                response = self.client.get(self.stat_video_url)
                self.assertContains(response, self.video.title.capitalize())
                self.assertNotContains(response, 'name="password"')
                response = self.client.post(self.stat_video_url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()[0]["slug"], self.video.slug)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_collective_statistics_filter_videos_and_earliest_date(self) -> None:
        """Collective statistics disclose only each viewer's authorized videos."""
        group = AccessGroup.objects.create(code_name="stats-collection")
        self.video.password = "StatsPassword"
        self.video.save()
        self.video2.is_restricted = True
        self.video2.save()
        self.video2.restrict_access_to_groups.add(group)
        self.video3.channel.add(self.channel)
        self.video3.theme.add(self.theme)
        older_date = self.video.date_added - timedelta(days=100)
        Video.objects.filter(pk__in=(self.video.pk, self.video2.pk)).update(
            date_added=older_date
        )
        urls = (
            reverse("video:video_stats_view"),
            self.stat_channel_url,
            self.stat_theme_url,
        )

        for audience in ("anonymous", "visitor", "group", "password", "owner"):
            expected_slugs = {self.video3.slug}
            expected_min_date = self.video3.date_added.date()
            if audience == "visitor":
                self.client.force_login(self.visitor)
            elif audience == "group":
                self.visitor.owner.accessgroup_set.add(group)
            elif audience == "password":
                response = self.client.post(
                    self.stat_video_url, {"password": self.video.password}
                )
                self.assertEqual(response.status_code, 200)
            elif audience == "owner":
                self.client.force_login(self.user)
            if audience in ("group", "password", "owner"):
                expected_slugs.add(self.video2.slug)
                expected_min_date = older_date.date()
            if audience in ("password", "owner"):
                expected_slugs.add(self.video.slug)

            for url in urls:
                with self.subTest(audience=audience, url=url):
                    response = self.client.post(url)
                    self.assertEqual(response.status_code, 200)
                    data = response.json()
                    self.assertEqual({row["slug"] for row in data[:-1]}, expected_slugs)
                    self.assertEqual(
                        data[-1], {"min_date": expected_min_date.isoformat()}
                    )

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_empty_authorized_collections_return_empty_statistics(self) -> None:
        """A collection with no accessible video must not leak its earliest date."""
        Video.objects.filter(
            pk__in=(self.video.pk, self.video2.pk, self.video3.pk)
        ).update(password="StatsPassword")
        for url in (
            reverse("video:video_stats_view"),
            self.stat_channel_url,
            self.stat_theme_url,
        ):
            for data in ({"password": "StatsPassword"}, {}):
                with self.subTest(url=url, data=data):
                    response = self.client.post(url, data)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json(), [{"min_date": None}])

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_individual_statistics_do_not_disclose_other_videos_earliest_date(
        self,
    ) -> None:
        """An individual response's date bounds must concern only its video."""
        Video.objects.filter(pk=self.video2.pk).update(
            date_added=self.video2.date_added - timedelta(days=100)
        )
        response = self.client.post(self.stat_video_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()[-1], {"min_date": self.video.date_added.date().isoformat()}
        )

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_individual_statistics_require_video_on_current_site(self) -> None:
        """Knowing a slug must not expose statistics belonging to another site."""
        other_site = Site.objects.create(domain="other-stats.example", name="Other")
        self.video.sites.set([other_site])
        for user in (self.visitor, self.superuser):
            self.client.force_login(user)
            for method in ("get", "post"):
                with self.subTest(user=user, method=method):
                    response = getattr(self.client, method)(self.stat_video_url)
                    self.assertEqual(response.status_code, 404)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_missing_video_returns_404_for_get_and_post(self) -> None:
        """A missing or unknown individual slug must never fall back to JSON."""
        urls = (
            reverse("video:video_stats_view") + "?from=video",
            reverse("video:video_stats_view", kwargs={"slug": "missing-video"})
            + "?from=video",
        )
        for url in urls:
            for method in ("get", "post"):
                with self.subTest(url=url, method=method):
                    response = getattr(self.client, method)(url)
                    self.assertEqual(response.status_code, 404)

    @skipUnless(USE_STATS_VIEW, "Require URL video_stats_view")
    def test_statistics_reject_unsupported_http_methods(self) -> None:
        """Only GET and POST may be used to request video statistics."""
        for method in ("head", "put", "patch", "delete", "options"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.stat_video_url)
                self.assertEqual(response.status_code, 405)

    def tearDown(self) -> None:
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
