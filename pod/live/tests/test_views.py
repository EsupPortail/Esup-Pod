"""
Unit tests for live views
"""
from django.conf import settings
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from pod.live.models import Building, Broadcaster, HeartBeat
from pod.video.models import Video
from pod.video.models import Type
from django.core.management import call_command

# from django.core.exceptions import PermissionDenied
import ast
from django.http import JsonResponse
import datetime
import pytz


if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


class LiveViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        user = User.objects.create(username="pod", password="podv2")
        building = Building.objects.create(name="bulding1")
        if FILEPICKER:
            homedir, created = UserFolder.objects.get_or_create(
                name="Home", owner=user
            )
            poster = CustomImageModel.objects.create(
                folder=homedir, created_by=user, file="blabla.jpg"
            )
        else:
            poster = CustomImageModel.objects.create(file="blabla.jpg")
        Broadcaster.objects.create(
            name="broadcaster1",
            poster=poster,
            url="http://test.live",
            status=True,
            is_restricted=True,
            building=building,
        )
        video_on_hold = Video.objects.create(
            title="VideoOnHold",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        Broadcaster.objects.create(
            name="broadcaster2",
            poster=poster,
            url="http://test2.live",
            status=True,
            is_restricted=False,
            video_on_hold=video_on_hold,
            building=building,
        )

        print(" --->  SetUp of liveViewsTestCase : OK !")

    def test_lives(self):
        self.client = Client()
        response = self.client.get("/live/")
        self.assertTemplateUsed(response, "live/lives.html")

        print("   --->  test_lives of liveViewsTestCase : OK !")

    def test_building(self):
        self.client = Client()
        self.user = User.objects.create(
            username="randomviewer", first_name="Jean", last_name="Viewer"
        )

        password = "password"
        self.superuser = User.objects.create_superuser(
            "myuser", "myemail@test.com", password
        )

        self.building = Building.objects.get(name="bulding1")
        response = self.client.get("/live/building/%s/" % self.building.id)

        self.assertRedirects(
            response,
            "%s?referrer=%s"
            % (settings.LOGIN_URL, "/live/building/%s/" % self.building.id),
            status_code=302,
            target_status_code=302,
        )

        # User logged in
        self.client.force_login(self.user)
        # Broadcaster restricted
        response = self.client.get("/live/building/%s/" % self.building.id)
        # self.assertRaises(PermissionDenied, response)
        self.assertEqual(response.status_code, 403)

        # User logged in
        self.client.force_login(self.superuser)
        # Broadcaster restricted
        response = self.client.get("/live/building/%s/" % self.building.id)
        self.assertTemplateUsed(response, "live/building.html")

        print("   --->  test_building of liveViewsTestCase : OK !")

    def test_heartbeat(self):
        self.client = Client()
        self.user = User.objects.create(
            username="randomviewer", first_name="Jean", last_name="Viewer"
        )
        response = self.client.get(
            "/live/ajax_calls/heartbeat/?key=testkey&liveid=1",
            {},
            False,
            False,
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, 200)

        data = {"viewers": 0, "viewers_list": []}
        expected_content = JsonResponse(data, safe=False).content
        exp_content = expected_content.decode("UTF-8")
        exp_content = ast.literal_eval(exp_content)

        resp_content = response.content.decode("UTF-8")
        resp_content = ast.literal_eval(resp_content)

        self.assertEqual(resp_content, exp_content)
        call_command("live_viewcounter")

        response = self.client.get(
            "/live/ajax_calls/heartbeat/?key=testkey&liveid=1",
            {},
            False,
            False,
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, 200)

        data = {"viewers": 1, "viewers_list": []}
        expected_content = JsonResponse(data, safe=False).content
        exp_content = expected_content.decode("UTF-8")
        exp_content = ast.literal_eval(exp_content)

        resp_content = response.content.decode("UTF-8")
        resp_content = ast.literal_eval(resp_content)

        self.assertEqual(resp_content, exp_content)

        self.client.force_login(self.user)
        response = self.client.get(
            "/live/ajax_calls/heartbeat/?key=testkeypod&liveid=1",
            {},
            False,
            False,
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, 200)
        call_command("live_viewcounter")

        response = self.client.get(
            "/live/ajax_calls/heartbeat/?key=testkeypod&liveid=1",
            {},
            False,
            False,
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, 200)

        data = {
            "viewers": 2,
            "viewers_list": [
                {
                    "first_name": "Jean",
                    "is_superuser": False,
                    "last_name": "Viewer",
                }
            ],
        }
        expected_content = JsonResponse(data, safe=False).content
        exp_content = expected_content.decode("UTF-8")
        exp_content = exp_content.replace("false", "False")
        exp_content = ast.literal_eval(exp_content)

        resp_content = response.content.decode("UTF-8")
        resp_content = resp_content.replace("false", "False")
        resp_content = ast.literal_eval(resp_content)

        self.assertEqual(resp_content, exp_content)

        hb1 = HeartBeat.objects.get(viewkey="testkey")
        hb2 = HeartBeat.objects.get(viewkey="testkeypod")

        paris_tz = pytz.timezone("Europe/Paris")
        # make heartbeat expire now
        hb1.last_heartbeat = paris_tz.localize(
            datetime.datetime(2012, 3, 3, 1, 30)
        )
        hb1.save()
        hb2.last_heartbeat = paris_tz.localize(
            datetime.datetime(2012, 3, 3, 1, 30)
        )
        hb2.save()

        call_command("live_viewcounter")

        broad = Broadcaster.objects.get(name="broadcaster1")
        self.assertEqual(broad.viewcount, 0)

        print("   --->  test_heartbeat of liveViewsTestCase : OK !")

    def test_video_live(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")

        # User not logged in
        # Broadcaster restricted
        self.broadcaster = Broadcaster.objects.get(name="broadcaster1")
        response = self.client.get("/live/%s/" % self.broadcaster.slug)
        self.assertRedirects(
            response,
            "%s?referrer=%s"
            % (settings.LOGIN_URL, "/live/%s/" % self.broadcaster.slug),
            status_code=302,
            target_status_code=302,
        )
        # Broadcaster not restricted
        self.broadcaster = Broadcaster.objects.get(name="broadcaster2")
        response = self.client.get("/live/%s/" % self.broadcaster.slug)
        self.assertTemplateUsed(response, "live/live.html")

        # User logged in
        self.client.force_login(self.user)
        # Broadcaster restricted
        self.broadcaster = Broadcaster.objects.get(name="broadcaster1")
        response = self.client.get("/live/%s/" % self.broadcaster.slug)
        self.assertTemplateUsed(response, "live/live.html")
        # Broadcaster not restricted
        self.broadcaster = Broadcaster.objects.get(name="broadcaster2")
        response = self.client.get("/live/%s/" % self.broadcaster.slug)
        self.assertTemplateUsed(response, "live/live.html")

        self.broadcaster.password = "password"
        self.broadcaster.save()
        response = self.client.get("/live/%s/" % self.broadcaster.slug)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"])

        print("   --->  test_video_live of liveViewsTestCase : OK !")
