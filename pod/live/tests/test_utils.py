import os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from pod.live.models import Building, Broadcaster, Event
from pod.video.models import Type

MEDIA_ROOT = getattr(settings, "MEDIA_ROOT", "")


class LiveTestUtils(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        building = Building.objects.create(name="building1")
        e_broad = Broadcaster.objects.create(
            name="broadcaster1", building=building, url="http://first.url", status=True
        )
        e_user = User.objects.create(username="user1")
        e_type = Type.objects.create(title="type1")
        Event.objects.create(
            title="event1",
            owner=e_user,
            broadcaster=e_broad,
            type=e_type,
        )

    def test_send_email(self):
        """Teste l'envoi d'email et les paramètres d'envoi."""
        from pod.live.utils import send_email_confirmation, get_bcc, get_cc

        event = Event.objects.get(id=1)

        bcc = get_bcc(1)
        self.assertEquals(bcc, [])
        print(" --->  test_utils get_bcc ok")

        expected = ["first", "second"]
        bcc = get_bcc(expected)
        self.assertEquals(bcc, expected)
        print(" --->  test_utils get_bcc liste or tuple ok")

        expected = "first"
        bcc = get_bcc(expected)
        self.assertEquals(bcc, expected.split())
        print(" --->  test_utils get_bcc string ok")

        expected = ["emailadduser1", "emailadduser2"]
        additional_user1 = User.objects.create(username="adduser1", email=expected[0])
        additional_user2 = User.objects.create(username="adduser2", email=expected[1])

        event.additional_owners.set([additional_user1, additional_user2])
        cc = get_cc(event)
        self.assertEquals(cc, expected)
        print(" --->  test_utils get_cc ok")

        # TODO test this for real
        send_email_confirmation(event)
        print(" --->  test_utils send_email_confirmation ok")

    def test_date_string_to_second(self):
        """Teste la conversion d'une chaine de caractère en nombre de secondes."""
        from pod.live.utils import date_string_to_second

        self.assertEquals(0, date_string_to_second("a"))
        self.assertEquals(0, date_string_to_second("1:1:1"))
        self.assertEquals(0, date_string_to_second("00:00:61"))
        self.assertEquals(0, date_string_to_second("00:61:00"))
        self.assertEquals(0, date_string_to_second("24:00:00"))
        self.assertEquals(0, date_string_to_second("00:00:00"))
        self.assertEquals(1, date_string_to_second("00:00:01"))
        self.assertEquals(60, date_string_to_second("00:01:00"))
        self.assertEquals(3600, date_string_to_second("01:00:00"))
        self.assertEquals(3661, date_string_to_second("01:01:01"))
        self.assertEquals(86399, date_string_to_second("23:59:59"))
        print(" --->  test_utils date_string_to_second ok")

    def test_get_event_id_and_broadcaster_id(self):
        """Teste la récupération et le renvoi des éléments 'idevent' et 'idbroadcaster' de la requête."""
        from pod.live.utils import get_event_id_and_broadcaster_id

        rf = RequestFactory()
        # GET
        request = rf.get("/", data={}, content_type="application/json")
        result = get_event_id_and_broadcaster_id(request)
        self.assertEqual(result, (None, None))

        request = rf.get("/", data={"idevent": "12"}, content_type="application/json")
        result = get_event_id_and_broadcaster_id(request)
        self.assertEqual(result, ("12", None))

        request = rf.get(
            "/", data={"idbroadcaster": "34"}, content_type="application/json"
        )
        result = get_event_id_and_broadcaster_id(request)
        self.assertEqual(result, (None, "34"))

        request = rf.get(
            "/",
            data={"idevent": "12", "idbroadcaster": "34"},
            content_type="application/json",
        )
        result = get_event_id_and_broadcaster_id(request)
        self.assertEqual(result, ("12", "34"))

        # POST
        request = rf.post("/", data={}, content_type="application/json")
        result = get_event_id_and_broadcaster_id(request)
        self.assertEqual(result, (None, None))

        request = rf.post("/", data={"idevent": "12"}, content_type="application/json")
        result = get_event_id_and_broadcaster_id(request)
        self.assertEqual(result, ("12", None))

        request = rf.post(
            "/", data={"idbroadcaster": "34"}, content_type="application/json"
        )
        result = get_event_id_and_broadcaster_id(request)
        self.assertEqual(result, (None, "34"))

        request = rf.post(
            "/",
            data={"idevent": "12", "idbroadcaster": "34"},
            content_type="application/json",
        )
        result = get_event_id_and_broadcaster_id(request)
        self.assertEqual(result, ("12", "34"))

        print(" --->  test_utils test_get_event_id_and_broadcaster_id ok")

    def test_check_size_not_changing(self):
        """Teste que la taille d'une ressource sur le filesystem ne change pas."""
        import threading
        from pod.live.utils import check_size_not_changing
        from time import sleep

        # Create a temporary file for testing
        resource_path = "thread_test_file.txt"
        with open(resource_path, "w") as file:
            file.write("some content")

        self.assertIsNone(check_size_not_changing(resource_path))
        print(" --->  test_utils test_check_size_not_changing Ok")

        # Start a separate thread that modifies the file size every x seconds
        def modify_file():
            modifications = 0

            while modifications < 10:
                with open(resource_path, "a+") as f:
                    f.write(" some more content " + str(modifications))
                    modifications += 1
                    sleep(0.8)

            # remove the temporary file
            os.unlink(resource_path)

        # Modify the file in a thread during 8 seconds
        thread = threading.Thread(target=modify_file)
        thread.start()

        # Check the size (should raise an exception)
        with self.assertRaises(Exception) as cm:
            check_size_not_changing(resource_path)

        # Verify that the exception was raised
        self.assertEqual(str(cm.exception), "checkFileSize aborted")
        print(" --->  test_utils test_check_size_not_changing Exception Ok")

    def test_check_exists(self):
        """Teste qu'une ressource existe sur le filesystem."""
        from pod.live.utils import check_exists, check_size_not_changing

        with self.assertRaises(Exception):
            check_exists("dirname", True, 2)
            print("   --->  test_exists checkDirExists exception: OK!")

        self.assertIsNone(check_exists(MEDIA_ROOT, True, 1))
        print("   --->  test_exists checkDirExists: OK!")

        test_file = os.path.join(MEDIA_ROOT, "test.log")
        with self.assertRaises(Exception):
            check_exists("filename", False, 2)
            print("   --->  test_exists checkFileExists exception: OK!")

        open(test_file, "a").close()
        self.assertIsNone(check_exists(test_file, False, 1))
        print("   --->  test_exists checkFileExists: OK!")

        self.assertIsNone(check_size_not_changing(test_file, 2))
        print("   --->  test_exists checkFileSize: OK!")

        os.unlink(test_file)

    def check_permission(self):
        # already tested in test_views.py file
        pass
