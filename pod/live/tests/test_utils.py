from django.test import TestCase
from django.contrib.auth.models import User
from pod.video.models import Type
from pod.live.models import Building, Broadcaster, Event


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

    def test_utils(self):
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
