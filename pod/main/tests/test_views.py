"""Esup-Pod unit tests for main views.

*  run with 'python manage.py test pod.main.tests.test_views'
"""

from django.test import RequestFactory, override_settings
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.flatpages.models import FlatPage
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.conf import settings
from captcha.models import CaptchaStore
from http import HTTPStatus
from datetime import datetime, timedelta
from pod.main import context_processors
from pod.main.models import Configuration, Block
from pod.playlist.models import Playlist
from pod.video.models import Type, Video, Channel, ViewCount
from pod.live.models import Building, Broadcaster, Event

import os
import importlib

# ggignore-start
# gitguardian:ignore
PWD = "pod1234pod"  # nosec
# ggignore-end


class MainViewsTestCase(TestCase):
    """Main views test cases."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Create fictive user who will make tests."""
        User.objects.create(username="pod", password=PWD)
        print(" --->  SetUp of MainViewsTestCase: OK!")

    @override_settings()
    def test_download_file(self) -> None:
        """Test download file."""
        self.client = Client()

        # GET method is used
        response = self.client.get("/download/")
        self.assertRaises(PermissionDenied)

        # POST method is used
        # filename is not set
        response = self.client.post("/download/")
        self.assertRaises(PermissionDenied)
        # Wrong filename --> not in MEDIA folder
        with self.assertRaises(ValueError):
            response = self.client.post("/download/", {"filename": "/etc/passwd"})

        # Good filename
        filename = os.path.join(settings.MEDIA_ROOT, "test/test_file.txt")
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, "test")):
            os.mkdir(os.path.join(settings.MEDIA_ROOT, "test"))
        f = open(filename, "w")
        f.write("ok")
        f.close()
        response = self.client.post("/download/", {"filename": "test/test_file.txt"})
        self.assertTrue(response.status_code in [200, 400])
        print("   --->  download_file of mainViewsTestCase: OK!")

    def test_contact_us(self) -> None:
        """Test the "contact us" form."""
        self.client = Client()

        # GET method is used.
        response = self.client.get("/contact_us/")
        self.assertTemplateUsed(response, "contact_us.html")

        # POST method is used
        # Form is valid
        hashcode = CaptchaStore.generate_key()
        captcha = CaptchaStore.objects.get(hashkey=hashcode)  # Forcing captcha
        response = self.client.post(
            "/contact_us/",
            {
                "name": "pod",
                "email": "pod@univ.fr",
                "subject": "info",
                "description": "pod",
                "captcha_0": captcha.hashkey,
                "captcha_1": captcha.response,
                "url_referrer": "http://pod.localhost:8000/",
                "firstname": "",
            },
        )
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), _("Your message has been sent."))
        self.assertRedirects(response, "http://pod.localhost:8000/")
        print("   --->  test_contact_us of mainViewsTestCase: OK!")
        # Form is not valid
        #  /!\  voir fonction clean de ContactUsForm segment if
        response = self.client.post(
            "/contact_us/",
            {
                "name": "",
                "email": "",
                "subject": "info",
                "description": "",
                "captcha": "",
                "firstname": "",
            },
        )
        self.assertTemplateUsed(response, "contact_us.html")
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), _("One or more errors have been found in the form.")
        )
        self.assertTemplateUsed(response, "contact_us.html")

        print("   --->  test_contact_us of mainViewsTestCase: OK!")


class MaintenanceViewsTestCase(TestCase):
    """TestCase for the maintenance view."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up function for the tests."""
        User.objects.create(username="pod", password=PWD)

    def test_maintenance(self) -> None:
        """Test Pod maintenance mode."""
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        # GET method is used
        url = reverse("video:video_edit", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        conf = Configuration.objects.get(key="maintenance_mode")
        conf.value = "1"
        conf.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/maintenance/")
        print("   --->  test_maintenance of MaintenanceViewsTestCase: OK!")


class RobotsTxtTests(TestCase):
    """Robots.txt test cases."""

    def test_robots_get(self) -> None:
        """Test if we get a robot.txt file."""
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")

    def test_robots_post_disallowed(self) -> None:
        """Test if POST method is disallowed when getting robot.txt file."""
        response = self.client.post("/robots.txt")

        self.assertEqual(HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)


class XSSTests(TestCase):
    """Tests against some Reflected XSS security breach."""

    def setUp(self) -> None:
        """Set up some generic test strings."""
        self.XSS_inject = "</script><script>alert(document.domain)</script>"
        self.XSS_detect = b"<script>alert(document.domain)</script>"

    def test_videos_XSS(self) -> None:
        """Test if /videos/ is safe against some XSS."""
        for param in ["owner", "discipline", "tag", "cursus"]:
            response = self.client.get("/videos/?%s=%s" % (param, self.XSS_inject))

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertFalse(self.XSS_detect in response.content)

    def test_search_XSS(self) -> None:
        """Test if /search/ is safe against some XSS."""
        for param in ["q", "start_date", "end_date"]:
            response = self.client.get("/search/?%s=%s" % (param, self.XSS_inject))

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertFalse(self.XSS_detect in response.content)

        # Test that even with a recognized facet it doesn't open a breach
        for facet in ["type", "slug"]:
            response = self.client.get(
                "/search/?selected_facets=%s:%s" % (facet, self.XSS_inject)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertFalse(self.XSS_detect in response.content)


class TestShowVideoButtons(TestCase):
    """`TestCase` for the video buttons."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up function for the tests."""
        self.factory = RequestFactory()
        User.objects.create(
            username="admin", password="admin", is_staff=True, is_superuser=True
        )
        User.objects.create(username="staff", password="staff", is_staff=True)
        User.objects.create(username="student", password="student", is_staff=False)

    @override_settings(RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=True)
    def test_show_video_buttons_admin_restrict(self) -> None:
        """
        Test if video buttons present in header for admins.

        If restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="admin")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-myvideos"' in response.content.decode())
        self.assertTrue('id="nav-addvideo"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=True)
    def test_show_video_buttons_staff_restrict(self) -> None:
        """
        Test if video buttons present in header for staff.

        If restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="staff")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-myvideos"' in response.content.decode())
        self.assertTrue('id="nav-addvideo"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=True)
    def test_show_video_buttons_student_restrict(self) -> None:
        """
        Test if video buttons not present in header for student.

        If restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="student")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse('id="nav-myvideos"' in response.content.decode())
        self.assertFalse('id="nav-addvideo"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=False)
    def test_show_video_buttons_admin_not_restrict(self) -> None:
        """
        Test if video buttons present in header for admin.

        If not restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="admin")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-myvideos"' in response.content.decode())
        self.assertTrue('id="nav-addvideo"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=False)
    def test_show_video_buttons_staff_not_restrict(self) -> None:
        """
        Test if video buttons present in header for staff.

        If not restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="staff")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-myvideos"' in response.content.decode())
        self.assertTrue('id="nav-addvideo"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=False)
    def test_show_video_buttons_student_not_restrict(self) -> None:
        """
        Test if video buttons present in header for student.

        If not restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="student")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-myvideos"' in response.content.decode())
        self.assertTrue('id="nav-addvideo"' in response.content.decode())
        self.client.logout()


class TestShowMeetingButton(TestCase):
    """`TestCase` for the meeting button."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up function for the tests."""
        self.factory = RequestFactory()
        User.objects.create(
            username="admin", password="admin", is_staff=True, is_superuser=True
        )
        User.objects.create(username="staff", password="staff", is_staff=True)
        User.objects.create(username="student", password="student", is_staff=False)

    @override_settings(RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY=True, USE_MEETING=True)
    def test_show_meeting_button_admin_restrict(self) -> None:
        """
        Test if meeting button present in header for admin.

        If restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="admin")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-mymeetings"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY=True, USE_MEETING=True)
    def test_show_meeting_button_staff_restrict(self) -> None:
        """
        Test if meeting button present in header for staff.

        If restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="staff")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-mymeetings"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY=True, USE_MEETING=True)
    def test_show_meeting_button_student_restrict(self) -> None:
        """
        Test if meeting button not present in header for student.

        If restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="student")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse('id="nav-mymeetings"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY=False, USE_MEETING=True)
    def test_show_meeting_button_admin_not_restrict(self) -> None:
        """
        Test if meeting button present in header for admin.

        If not restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="admin")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-mymeetings"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY=False, USE_MEETING=True)
    def test_show_meeting_button_staff_not_restrict(self) -> None:
        """
        Test if meeting button present in header for staff.

        If not restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="staff")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-mymeetings"' in response.content.decode())
        self.client.logout()

    @override_settings(RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY=False, USE_MEETING=True)
    def test_show_meeting_button_student_not_restrict(self) -> None:
        """
        Test if meeting button not present in header for student.

        If not restrict access to staff only.
        """
        importlib.reload(context_processors)
        self.user = User.objects.get(username="student")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id="nav-mymeetings"' in response.content.decode())
        self.client.logout()


class TestNavbar(TestCase):
    """Navbar tests case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.user = User.objects.create(username="pod", password="pod1234pod")

    @override_settings(USE_FAVORITES=False)
    def test_statistics_category_hidden(self) -> None:
        """Test if statistics are hidden when we don't have stats."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get("/")

        self.assertFalse(
            'id="stats-usermenu"' in response.content.decode(),
            "test if statistics section is correctly hidden",
        )
        print(" --->  test_statistics_category_hidden ok")

    @override_settings(USE_FAVORITES=False)
    def test_statistics_videos(self) -> None:
        """Test if videos statistics are correctly shown."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        # We create a playlist to show statistics section in usermenu
        Playlist.objects.create(
            name="public_playlist_user",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user,
        )

        response = self.client.get("/")
        self.assertFalse(
            'id="stats-usermenu-video-count"' in response.content.decode(),
            "test if video count paragraph is correctly hidden",
        )

        Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        Video.objects.create(
            title="Video2",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        response = self.client.get("/")
        self.assertTrue(
            '<span id="stats-usermenu-video-count">2' in response.content.decode(),
            "test if number of videos is correct",
        )
        print(" --->  test_statistics_videos ok")

    @override_settings(USE_PLAYLIST=True, USE_FAVORITES=False)
    def test_statistics_playlists(self) -> None:
        """Test if playlists statistics are correctly shown."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)

        # We create a video to show statistics section in usermenu
        Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

        response = self.client.get("/")
        self.assertFalse(
            'id="stats-usermenu-playlist-count"' in response.content.decode(),
            "test if video count paragraph is correctly hidden",
        )

        Playlist.objects.create(
            name="playlist_1",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user,
        )
        Playlist.objects.create(
            name="playlist_2",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user,
        )
        response = self.client.get("/")
        self.assertTrue(
            '<span id="stats-usermenu-playlist-count">2' in response.content.decode(),
            "test if number of playlists is correct.",
        )

        print(" --->  test_statistics_playlists ok")

    @override_settings(WEBTV_MODE=True)
    def test_login_button_hidden(self) -> None:
        """Test if login button is hidden when the webtv mode is true."""
        importlib.reload(context_processors)
        response = self.client.get("/")
        self.assertFalse(
            'id="nav-authentication"' in response.content.decode(),
            "test if login button is correctly hidden",
        )


class TestBlock(TestCase):
    """Block tests case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up Block tests."""
        print(" --->  init blocktest ok")

    def test_html_block_content(self) -> None:
        """Test html block."""
        bl2 = Block.objects.create(
            title="block html",
            type="html",
            page=FlatPage.objects.get(id=1),
            html="<p>MaChaineDeTest</p>",
            no_cache=True,
            visible=True,
        )
        self.client = Client()
        response = self.client.get("/")
        self.assertTrue(
            "<p>MaChaineDeTest</p>" in response.content.decode(),
            "test if block html is present.",
        )
        bl2.visible = False
        bl2.save()
        response = self.client.get("/")
        self.assertFalse(
            "<p>MaChaineDeTest</p>" in response.content.decode(),
            "test if block html is not present.",
        )
        bl2.visible = True
        bl2.must_be_auth = True
        bl2.save()
        response = self.client.get("/")
        self.assertFalse(
            "<p>MaChaineDeTest</p>" in response.content.decode(),
            "test if block html is not present.",
        )

        User.objects.create(username="test", password="azerty")
        self.user = User.objects.get(username="test")
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertTrue(
            "<p>MaChaineDeTest</p>" in response.content.decode(),
            "test if block html is present.",
        )

        print(" --->  test_Block_Html ok")

    def test_default_block(self) -> None:
        """Test when add video if present in default block."""
        user = User.objects.create(username="pod", password=PWD)
        Video.objects.create(
            title="VideoOnHold",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
            is_draft=False,
            slug="video-on-hold",
            duration=20,
            date_added=datetime.today(),
            encoding_in_progress=False,
            date_evt=datetime.today(),
        )
        self.client = Client()
        response = self.client.get("/")
        self.assertTrue(
            "VideoOnHold" in response.content.decode(),
            "test if video VideoOnHold is present.",
        )
        print(" --->  test_Video_in_default_block ok")

    def test_channel_type_block(self) -> None:
        """Test if create channel with video, this video is present in block type channel."""
        bk1 = Block.objects.get(id=1)
        bk1.visible = False
        bk1.save()
        channel = Channel.objects.create(title="monChannel")
        user = User.objects.create(username="pod", password=PWD)
        video = Video.objects.create(
            title="VideoOnHold",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
            is_draft=False,
            slug="video-on-hold",
            duration=20,
            date_added=datetime.today(),
            encoding_in_progress=False,
            date_evt=datetime.today(),
        )
        video.channel.add(channel)
        bl2 = Block.objects.create(
            title="block channel",
            type="carousel",
            page=FlatPage.objects.get(id=1),
            data_type="channel",
            Channel=Channel.objects.get(id=1),
            no_cache=True,
            visible=True,
            view_videos_from_non_visible_channels=False,
        )

        self.client = Client()
        response = self.client.get("/")

        self.assertFalse(
            "VideoOnHold" in response.content.decode(),
            "test if video VideoOnHold is not present.",
        )

        bl2.view_videos_from_non_visible_channels = True
        bl2.save()
        response = self.client.get("/")

        self.assertTrue(
            "VideoOnHold" in response.content.decode(),
            "test if video VideoOnHold is present.",
        )

        bl2.view_videos_from_non_visible_channels = False
        bl2.save()
        channel.visible = True
        channel.save()
        response = self.client.get("/")

        self.assertTrue(
            "VideoOnHold" in response.content.decode(),
            "test if video VideoOnHold is present.",
        )
        self.assertTrue(
            '<div class="pod-inner edito-carousel">' in response.content.decode(),
            "test if type block is carousel.",
        )
        print(" --->  test_Video_in_channel_block ok")

    def test_next_events_type_block(self) -> None:
        """Test if create create next event present in block type next events."""
        building = Building.objects.create(name="building1")
        broad = Broadcaster.objects.create(
            name="broadcaster1",
            url="http://test.live",
            status=True,
            is_restricted=True,
            building=building,
            public=False,
        )
        user = User.objects.create(username="pod")
        h_type = Type.objects.create(title="type1")
        event = Event.objects.create(
            title="MonEventDeTest",
            owner=user,
            broadcaster=broad,
            type=h_type,
            is_draft=False,
        )
        event.start_date = datetime.today() + timedelta(days=+1)
        event.end_date = datetime.today() + timedelta(days=+2)
        event.save()

        Block.objects.create(
            title="block next events",
            type="card_list",
            page=FlatPage.objects.get(id=1),
            data_type="event_next",
            no_cache=True,
            visible=True,
        )
        self.client = Client()
        response = self.client.get("/")
        self.assertTrue(
            "MonEventDeTest" in response.content.decode(),
            "test if event MonEventDeTest is present.",
        )
        self.assertTrue(
            '<div class="pod-inner edito-card-list"' in response.content.decode(),
            "test if block is card list.",
        )
        print(" --->  test_Next_Event_in_Block_next_event_type ok")

    def test_most_views_type_block(self) -> None:
        """Test if most views video is present in block type most view."""
        bk1 = Block.objects.get(id=1)
        bk1.visible = False
        bk1.save()
        user = User.objects.create(username="pod", password=PWD)
        vd1 = Video.objects.create(
            title="VideoOnHold",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
            is_draft=False,
            slug="video-on-hold",
            duration=20,
            encoding_in_progress=False,
        )
        ViewCount.objects.create(video=vd1, date=datetime.today(), count=1)
        Block.objects.create(
            title="block most views",
            type="multi_carousel",
            page=FlatPage.objects.get(id=1),
            data_type="most_views",
            no_cache=True,
            visible=True,
        )
        self.client = Client()
        response = self.client.get("/")
        self.assertTrue(
            "VideoOnHold" in response.content.decode(),
            "test if video VideoOnHold is present.",
        )
        self.assertTrue(
            '<div class="pod-inner edito-multi-carousel">' in response.content.decode(),
            "test if block is carousel multi.",
        )
        print(" --->  test_Video_in_type_most_views_block ok")
