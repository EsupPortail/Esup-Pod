"""
Unit tests for live views
"""
import ast
import httmock
import pytz
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.http import JsonResponse, Http404
from django.test import Client
from django.test import TestCase, override_settings
from httmock import HTTMock, all_requests
from pod.live.forms import EventForm
from pod.live.models import Building, Broadcaster, HeartBeat, Event
from pod.video.models import Type
from pod.video.models import Video

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
            homedir, created = UserFolder.objects.get_or_create(name="Home", owner=user)
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
            piloting_implementation="wowza",
            piloting_conf='{"server_url": "http://mock_api.fr", "application": "mock_name", "livestream": "mock_livestream"}',
        )
        Event.objects.create(
            title="event1",
            owner=user,
            is_restricted=True,
            is_draft=True,
            broadcaster=Broadcaster.objects.get(id=1),
            type=Type.objects.get(id=1),
        )

        print(" --->  SetUp of liveViewsTestCase : OK !")

    def test_lives(self):
        # User not logged in
        with self.settings(USE_EVENT=False):
            response = self.client.get("/live/")
            self.assertTemplateUsed(response, "live/lives.html")
            print("   --->  test_lives of liveViewsTestCase : OK !")

        with self.settings(USE_EVENT=True):
            self.client = Client()
            response = self.client.get("/live/")
            self.assertEqual(response.status_code, 403)
            print("   --->  test_lives of liveViewsTestCase : OK !")

        # Admin
        self.superuser = User.objects.create_superuser(
            "myuser", "myemail@test.com", "superpassword"
        )
        self.client.force_login(self.superuser)
        response = self.client.get("/live/")
        self.assertTemplateUsed(response, "live/lives.html")
        print("   --->  test_lives of liveViewsTestCase : OK !")

        broad = Broadcaster.objects.get(name="broadcaster1")
        response = self.client.get("/live/%s/" % broad.slug)
        self.assertTemplateUsed(response, "live/events_list.html")
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
        hb1.last_heartbeat = paris_tz.localize(datetime(2012, 3, 3, 1, 30))
        hb1.save()
        hb2.last_heartbeat = paris_tz.localize(datetime(2012, 3, 3, 1, 30))
        hb2.save()

        call_command("live_viewcounter")

        broad = Broadcaster.objects.get(name="broadcaster1")
        self.assertEqual(broad.viewcount, 0)

        print("   --->  test_heartbeat of liveViewsTestCase : OK !")

    @override_settings(USE_EVENT=False)
    def test_video_live(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")

        # User not logged in
        # Broadcaster restricted
        with self.settings(USE_EVENT=True):
            self.broadcaster = Broadcaster.objects.get(name="broadcaster1")
            response = self.client.get("/live/%s/" % self.broadcaster.slug)
            self.assertEqual(response.status_code, 403)

        self.broadcaster = Broadcaster.objects.get(name="broadcaster1")
        response = self.client.get("/live/%s/" % self.broadcaster.slug)
        self.assertRedirects(
            response,
            "%s?referrer=%s" % (settings.LOGIN_URL, "/live/%s/" % self.broadcaster.slug),
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

    def test_events(self):
        self.client = Client()

        # User not logged in
        response = self.client.get("/")
        self.assertTemplateUsed(response, "live/events_next.html")
        print("   --->  test_events of / : OK !")

        response = self.client.get("/live/events/")
        self.assertTemplateUsed(response, "live/events.html")
        print("   --->  test_events of live/events : OK !")

        response = self.client.get("/live/events/?page=100")
        self.assertTemplateUsed(response, "live/events.html")
        print("   --->  test_events of live/events paginator empty: OK !")

        response = self.client.get("/live/events/?page=notint")
        self.assertTemplateUsed(response, "live/events.html")
        print("   --->  test_events of live/events paginator not integer: OK !")

        response = self.client.get("/live/my_events/")
        self.assertRedirects(
            response,
            "%s?referrer=%s" % (settings.LOGIN_URL, "/live/my_events/"),
            status_code=302,
            target_status_code=302,
        )
        print("   --->  test_events of live/my_events : OK !")

        # event restricted and draft
        self.event = Event.objects.get(title="event1")
        response = self.client.get("/live/event/%s/" % self.event.slug)
        self.assertRedirects(
            response,
            "%s?referrer=%s" % (settings.LOGIN_URL, "/live/event/%s/" % self.event.slug),
            status_code=302,
            target_status_code=302,
        )
        print("   --->  test_events access restricted event : OK !")

        # event not restricted but draft (permission denied)
        self.event.is_restricted = False
        self.event.is_draft = True
        self.event.save()
        response = self.client.get("/live/event/%s/" % self.event.slug)
        self.assertEqual(response.status_code, 403)
        print("   --->  test_events access not restricted but draft event : OK !")

        # event not restricted but draft (shared link)
        response = self.client.get(
            "/live/event/%s/%s/" % (self.event.slug, self.event.get_hashkey())
        )
        self.assertTemplateUsed(response, "live/event.html")
        print(
            "   --->  test_events access not restricted but draft with public link event : OK !"
        )

        # event restricted and not draft (permission denied)
        self.event.is_restricted = True
        self.event.is_draft = False
        self.event.save()
        response = self.client.get("/live/event/%s/" % self.event.slug)
        self.assertRedirects(
            response,
            "%s?referrer=%s" % (settings.LOGIN_URL, "/live/event/%s/" % self.event.slug),
            status_code=302,
            target_status_code=302,
        )
        print("   --->  test_events access restricted and not draft event : OK !")

        # event not restricted nor draft
        self.event.is_restricted = False
        self.event.is_draft = False
        self.event.save()
        response = self.client.get("/live/event/%s/" % self.event.slug)
        self.assertTemplateUsed(response, "live/event.html")
        print("   --->  test_events access not restricted nor draft event : OK !")

        response = self.client.get(
            "/live/event/%s/" % self.event.slug, {"is_iframe": True}
        )
        self.assertTemplateUsed(response, "live/event-iframe.html")
        print("   --->  test_events access not restricted nor draft iframe event : OK !")

        # event creation
        response = self.client.get("/live/event_edit/")
        self.assertRedirects(
            response,
            "%s?referrer=%s" % (settings.LOGIN_URL, "/live/event_edit/"),
            status_code=302,
            target_status_code=302,
        )
        print("   --->  test_events creation event : OK !")

        # User logged in (and Staff)
        self.user = User.objects.create(username="johndoe", password="johnpwd")
        self.client.force_login(self.user)

        response = self.client.get("/live/my_events/")
        self.assertTemplateUsed(response, "live/my_events.html")
        print("   --->  test_events of live/my_events : OK !")

        response = self.client.get("/live/my_events/?ppage=100")
        self.assertTemplateUsed(response, "live/my_events.html")
        print("   --->  test_events of live/my_events paginator empty: OK !")

        response = self.client.get("/live/my_events/?ppage=notint")
        self.assertTemplateUsed(response, "live/my_events.html")
        print("   --->  test_events of live/my_events paginator not integer: OK !")

        # event restricted and draft (permission denied)
        self.event = Event.objects.get(title="event1")
        self.event.is_restricted = True
        self.event.is_draft = True
        self.event.save()
        response = self.client.get("/live/event/%s/" % self.event.slug)
        self.assertEqual(response.status_code, 403)
        print("   --->  test_events access restricted and draft with logged user : OK !")

        # event restricted but not draft
        self.event.is_draft = False
        self.event.save()
        response = self.client.get("/live/event/%s/" % self.event.slug)
        self.assertTemplateUsed(response, "live/event.html")
        print("   --->  test_events access restricted not draft with logged user : OK !")

        # wrong event id
        response = self.client.get("/live/event/what-ever/")
        self.assertEqual(400, response.status_code)
        print("  --->  test_events access nonexistent event : OK !")

        # event creation
        response = self.client.get("/live/event_edit/")
        self.assertTemplateUsed(response, "live/event_edit.html")
        print("   --->  test_events creation event : OK !")

        # event edition (access_not_allowed)
        response = self.client.get("/live/event_edit/%s/" % self.event.slug)
        self.assertTemplateUsed(response, "live/event_edit.html")
        self.assertEqual(response.context["access_not_allowed"], True)
        print("   --->  test_events edit event access_not_allowed : OK !")

        # event delete (permission denied)
        response = self.client.post("/live/event_delete/%s/" % self.event.slug)
        self.assertEqual(response.status_code, 403)
        print("   --->  test_events delete event : OK !")

        # User is event's owner
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)

        self.event = Event.objects.get(title="event1")
        self.event.is_restricted = True
        self.event.is_draft = True
        self.event.save()

        # myevents contains the event
        response = self.client.get("/live/my_events/")
        self.assertTemplateUsed(response, "live/my_events.html")
        self.assertTemplateUsed(response, "live/events_list.html")
        print("   --->  test_events owner sees his event's list: OK !")

        # user's event (restricted and draft)
        response = self.client.get("/live/event/%s/" % self.event.slug)
        self.assertTemplateUsed(response, "live/event.html")
        print("   --->  test_events access of restricted event for owner: OK !")

        # user's event edition
        response = self.client.get("/live/event_edit/%s/" % self.event.slug)
        self.assertTemplateUsed(response, "live/event_edit.html")
        self.assertIsInstance(response.context["form"], EventForm)
        print("   --->  test_events edit event for owner : OK !")

        # User is now staff
        self.user.is_staff = True
        self.user.save()

        response = self.client.get("/live/event_edit/%s/" % self.event.slug)
        self.assertTemplateUsed(response, "live/event_edit.html")
        self.assertIsInstance(response.context["form"], EventForm)
        print("   --->  test_events edit event for staff : OK !")

        response = self.client.get("/live/event/%s/" % self.event.slug)
        self.assertTemplateUsed(response, "live/event.html")
        self.assertTrue(response.context["need_piloting_buttons"])
        print("   --->  test_events need_piloting_buttons event for staff: OK !")

        # Superuser logged in
        self.superuser = User.objects.create_superuser(
            "myuser", "myemail@test.com", "superpassword"
        )
        self.client.force_login(self.superuser)

        # response = self.client.get("/")
        # self.assertTemplateUsed(response, "live/events_next.html")

        # event edition
        response = self.client.post("/live/event_edit/%s/" % self.event.slug)
        self.assertTemplateUsed(response, "live/event_edit.html")
        self.assertIsInstance(response.context["form"], EventForm)
        print("   --->  test_events edit event for superuser : OK !")

        # event delete
        response = self.client.post("/live/event_delete/%s/" % self.event.slug)
        self.assertTemplateUsed(response, "live/event_delete.html")
        print("   --->  test_events delete event for superuser : OK !")

    def test_get_broadcaster_by_slug(self):
        from pod.live.views import get_broadcaster_by_slug

        broadcaster = Broadcaster.objects.get(id=1)
        site = broadcaster.building.sites.first()

        broad = get_broadcaster_by_slug(1, site)
        self.assertEqual(broad, broadcaster)
        print("   --->  test get_broadcaster_by_slug : OK !")

        with self.assertRaises(Http404):
            get_broadcaster_by_slug(1, None)
        print("   --->  test get_broadcaster_by_slug No Site : OK !")

        with self.assertRaises(Http404):
            get_broadcaster_by_slug(-1, site)
        print("   --->  test get_broadcaster_by_slug Http404 : OK !")

    def test_broadcasters_from_building(self):
        url = "/live/ajax_calls/getbroadcastersfrombuiding/"
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 400)
        print("   --->  test broadcasters_from_building HttpResponseBadRequest : OK !")

        response = self.client.get(url, {"building": "nonexistant"})
        self.assertEqual(response.status_code, 404)
        print("   --->  test broadcasters_from_building HttpResponseBadRequest : OK !")

        response = self.client.get(url, {"building": "bulding1"})
        self.assertEqual(response.status_code, 200)
        print("   --->  test broadcasters_from_building : OK !")

        # log as superUser to get all Broadcaster of building1
        self.superuser = User.objects.create_superuser(
            "myuser", "myemail@test.com", "superpassword"
        )
        self.client.force_login(self.superuser)

        response = self.client.get(url, {"building": "bulding1"})
        self.assertEqual(response.status_code, 200)
        expected = {
            "1": {"id": 1, "name": "broadcaster1", "restricted": True},
            "2": {"id": 2, "name": "broadcaster2", "restricted": False},
        }
        self.assertEqual(response.json(), expected)
        print("   --->  test broadcasters_from_building all : OK !")

    def test_broadcaster_restriction(self):
        url = "/live/ajax_calls/getbroadcasterrestriction/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        print("   --->  test broadcaster_restriction HttpResponseNotAllowed : OK !")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        print("   --->  test broadcaster_restriction HttpResponseBadRequest : OK !")

        response = self.client.get(url, {"idbroadcaster": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"restricted": True})
        print("   --->  test broadcaster_restriction : OK !")

    def test_isstreamavailabletorecord(self):
        url = "/live/event_isstreamavailabletorecord/"
        # not logged
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        print("   --->  test isstreamavailabletorecord user not logged : OK !")

        # user logged
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        print("   --->  test isstreamavailabletorecord HttpResponseNotAllowed : OK !")

        response = self.client.get(
            url, {"idbroadcaster": 1}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.json(), {'available': False, 'recording': False, 'message': 'implementation error'})
        print("   --->  test isstreamavailabletorecord implementation error : OK !")

    def test_start_record(self):
        url = "/live/ajax_calls/event_startrecord/"

        # not logged
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        print("   --->  test startrecord user not logged : OK !")

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        print("   --->  test startrecord HttpResponseNotAllowed : OK !")

        response = self.client.post(
            url,
            {"idbroadcaster": 1, "idevent": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.json(), {'success': False, 'message': 'implementation error'})
        print("   --->  test startrecord implementation error : OK !")

    def test_split_record(self):
        url = "/live/ajax_calls/event_splitrecord/"

        # not logged
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        print("   --->  test splitrecord user not logged : OK !")

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        print("   --->  test splitrecord HttpResponseNotAllowed : OK !")

        response = self.client.post(
            url,
            {"idbroadcaster": 1, "idevent": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        print("   --->  test splitrecord implementation error : OK !")

    def test_stop_record(self):
        url = "/live/ajax_calls/event_stoprecord/"

        # not logged
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        print("   --->  test stoprecord user not logged : OK !")

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        print("   --->  test stoprecord HttpResponseNotAllowed : OK !")

        response = self.client.post(
            url,
            {"idbroadcaster": 1, "idevent": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        print("   --->  test stoprecord implementation error : OK !")

    def test_event_info_record(self):
        url = "/live/ajax_calls/geteventinforcurrentecord/"

        # not logged
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        print("   --->  test event_info_record user not logged : OK !")

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        print("   --->  test event_info_record HttpResponseNotAllowed : OK !")

        response = self.client.post(
            url,
            {"idbroadcaster": 1, "idevent": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        print("   --->  test event_info_record implementation error : OK !")

        # Brodacaster with implementation parameters
        @all_requests
        def response_is_recording_ko(url, request):
            return httmock.response(
                200,
                {
                    "isConnected": False,
                    "isRecordingSet": False,
                },
            )

        @all_requests
        def response_is_recording_ok(url, request):
            return httmock.response(
                200,
                {
                    "isConnected": True,
                    "isRecordingSet": True,
                    "segmentDuration": 3000,
                },
            )

        with HTTMock(response_is_recording_ko):
            response = self.client.post(
                url,
                {"idbroadcaster": 2, "idevent": 1},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(
            response.json(),
            {"success": False, "error": "the broadcaster is not recording"},
        )
        print("   --->  test event_info_record not recording : OK !")

        with HTTMock(response_is_recording_ok):
            response = self.client.post(
                url,
                {"idbroadcaster": 2, "idevent": 1},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
        self.assertEqual(response.json(), {"success": True, "duration": 3})
        print("   --->  test event_info_record recording : OK !")

    def test_is_recording(self):
        from pod.live.views import is_recording

        broadcaster = Broadcaster.objects.get(id=1)
        broad_with_impl = Broadcaster.objects.get(id=2)

        # is_recording
        @all_requests
        def response_is_recording_ko(url, request):
            return httmock.response(
                200,
                {
                    "isConnected": False,
                    "isRecordingSet": False,
                },
            )

        @all_requests
        def response_is_recording_ok(url, request):
            return httmock.response(
                200,
                {
                    "isConnected": True,
                    "isRecordingSet": True,
                },
            )

        response = is_recording(broadcaster)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster is_recording no impl : OK !")

        with HTTMock(response_is_recording_ko):
            response = is_recording(broad_with_impl, False)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster is_recording no : OK !")

        with HTTMock(response_is_recording_ok):
            response = is_recording(broad_with_impl, False)
        self.assertTrue(response)
        print("   --->  test misc_broadcaster is_recording yes : OK !")

    def test_is_available_to_record(self):
        from pod.live.views import is_available_to_record

        broadcaster = Broadcaster.objects.get(id=1)
        broad_with_impl = Broadcaster.objects.get(id=2)

        # is_available_to_record
        @all_requests
        def response_is_available_to_record_ok(url, request):
            return httmock.response(200, {"isConnected": True, "isRecordingSet": False})

        @all_requests
        def response_is_recording_ok(url, request):
            return httmock.response(
                200,
                {
                    "isConnected": True,
                    "isRecordingSet": True,
                },
            )

        response = is_available_to_record(broadcaster)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster is_available_to_record no impl: OK !")

        with HTTMock(response_is_recording_ok):
            response = is_available_to_record(broad_with_impl)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster is_available_to_record no : OK !")

        with HTTMock(response_is_available_to_record_ok):
            response = is_available_to_record(broad_with_impl)
        self.assertTrue(response)
        print("   --->  test misc_broadcaster is_available_to_record yes : OK !")

    def test_method_start_record(self):
        from pod.live.views import start_record

        broadcaster = Broadcaster.objects.get(id=1)
        broad_with_impl = Broadcaster.objects.get(id=2)

        @all_requests
        def response_created_ko(url, request):
            return httmock.response(201, {"success": False})

        @all_requests
        def response_created_ok(url, request):
            return httmock.response(201, {"success": True})

        response = start_record(broadcaster, 1)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster start_record no impl : OK !")

        with HTTMock(response_created_ko):
            response = start_record(broad_with_impl, 1)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster start_record no : OK !")

        with HTTMock(response_created_ok):
            response = start_record(broad_with_impl, 1)
        self.assertTrue(response)
        print("   --->  test misc_broadcaster start_record yes  : OK !")

    def test_method_split_record(self):
        from pod.live.views import split_record

        broadcaster = Broadcaster.objects.get(id=1)
        broad_with_impl = Broadcaster.objects.get(id=2)

        @all_requests
        def response_ko(url, request):
            return httmock.response(200, {"success": False})

        @all_requests
        def response_ok(url, request):
            return httmock.response(200, {"success": True})

        response = split_record(broadcaster)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster split_record no impl : OK !")

        with HTTMock(response_ko):
            response = split_record(broad_with_impl)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster split_record no : OK !")

        with HTTMock(response_ok):
            response = split_record(broad_with_impl)
        self.assertTrue(response)
        print("   --->  test misc_broadcaster split_record yes : OK !")

    def test_method_stop_record(self):
        from pod.live.views import stop_record

        broadcaster = Broadcaster.objects.get(id=1)
        broad_with_impl = Broadcaster.objects.get(id=2)

        @all_requests
        def response_ko(url, request):
            return httmock.response(200, {"success": False})

        @all_requests
        def response_ok(url, request):
            return httmock.response(200, {"success": True})

        response = stop_record(broadcaster)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster stop_record no impl : OK !")

        with HTTMock(response_ko):
            response = stop_record(broad_with_impl)
        self.assertFalse(response)
        print("   --->  test misc_broadcaster stop_record no : OK !")

        with HTTMock(response_ok):
            response = stop_record(broad_with_impl)
        self.assertTrue(response)
        print("   --->  test misc_broadcaster stop_record yes : OK !")

    def test_method_info_current_record(self):
        from pod.live.views import get_info_current_record

        broadcaster = Broadcaster.objects.get(id=1)
        broad_with_impl = Broadcaster.objects.get(id=2)

        @all_requests
        def response_info_current_record_ko(url, request):
            return httmock.response(400, {"content": ""})

        @all_requests
        def response_info_current_record_ok(url, request):
            return httmock.response(
                200,
                {
                    "currentFile": "file_10.mp3",
                    "segmentNumber": "23",
                    "outputPath": "aa",
                    "segmentDuration": "60",
                },
            )

        expected_on_error = {
            "currentFile": "",
            "segmentNumber": "",
            "outputPath": "",
            "segmentDuration": "",
        }
        response = get_info_current_record(broadcaster)
        self.assertEqual(response, expected_on_error)
        print("   --->  test misc_broadcaster get_info_current_record no impl: OK !")

        with HTTMock(response_info_current_record_ko):
            response = get_info_current_record(broad_with_impl)
        self.assertEqual(response, expected_on_error)
        print("   --->  test misc_broadcaster get_info_current_record error : OK !")

        with HTTMock(response_info_current_record_ok):
            response = get_info_current_record(broad_with_impl)
        self.assertEqual(
            response,
            {
                "currentFile": "file_10.mp3",
                "segmentNumber": "10",
                "outputPath": "aa",
                "segmentDuration": "60",
            },
        )
        print("   --->  test misc_broadcaster get_info_current_record ok : OK !")

    def test_event_video_cards(self):
        url = "/live/ajax_calls/geteventvideocards/"

        # not ajax
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        print("   --->  test event_video_cards not ajax : OK !")

        response = self.client.get(
            url, {"idevent": 1}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.json(), {"content": ""})
        print("   --->  test event_video_cards empty : OK !")

        video = Video.objects.get(id=1)
        event = Event.objects.get(id=1)
        event.videos.add(video)
        event.save()

        response = self.client.get(
            url, {"idevent": 1}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json(), {"content": ""})
        print("   --->  test event_video_cards with videos : OK !")

    def test_event_dir_exists(self):
        from pod.live.views import checkDirExists, checkFileExists

        with self.assertRaises(Exception):
            checkDirExists("dirname", 2)
            print("   --->  test checkDirExists exception : OK !")

        with self.assertRaises(Exception):
            checkFileExists("filename", 2)
            print("   --->  test checkFileExists exception : OK !")
