from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import BBB_Meeting as Meeting, Attendee, Livestream


class MeetingTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        Meeting.objects.create(
            id=1,
            meeting_id="id1",
            internal_meeting_id="internalid1",
            meeting_name="Session BBB1",
            encoding_step=0,
        )

        user = User.objects.create(username="pod")
        Meeting.objects.create(
            id=2,
            meeting_id="id2",
            internal_meeting_id="internalid2",
            meeting_name="Session BBB2",
            encoding_step=1,
            encoded_by=user,
        )

        print(" --->  SetUp of MeetingTestCase : OK !")

    # Test attributes
    def test_attributes(self):
        meeting = Meeting.objects.get(id=1)
        self.assertEqual(meeting.meeting_name, "Session BBB1")
        self.assertEqual(meeting.internal_meeting_id, "internalid1")
        self.assertEqual(meeting.meeting_name, "Session BBB1")
        self.assertEqual(meeting.encoding_step, 0)
        date = timezone.now()
        self.assertEqual(meeting.session_date.year, date.year)
        self.assertEqual(meeting.session_date.month, date.month)
        self.assertEqual(meeting.session_date.day, date.day)

        user = User.objects.get(username="pod")
        meeting2 = Meeting.objects.get(id=2)
        self.assertEqual(meeting2.meeting_name, "Session BBB2")
        self.assertEqual(meeting2.internal_meeting_id, "internalid2")
        self.assertEqual(meeting2.meeting_name, "Session BBB2")
        self.assertEqual(meeting2.encoding_step, 1)
        self.assertEqual(meeting2.encoded_by, user)
        print("   --->  test_attributs of MeetingTestCase : OK !")

    # Test update attributes
    def test_update_attributes(self):
        meeting = Meeting.objects.get(id=1)
        user = User.objects.get(username="pod")
        meeting.encoding_step = 1
        meeting.encoded_by = user
        meeting.save()
        self.assertEqual(meeting.encoding_step, 1)
        self.assertEqual(meeting.encoded_by, user)
        print("   --->  test_update_attributes of MeetingTestCase : OK !")

    # Test delete object
    def test_delete_object(self):
        Meeting.objects.filter(meeting_id="id1").delete()
        self.assertEquals(Meeting.objects.all().count(), 1)
        Meeting.objects.filter(meeting_id="id2").delete()
        self.assertEquals(Meeting.objects.all().count(), 0)

        print("   --->  test_delete_object of MeetingTestCase : OK !")


class AttendeeTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        meeting1 = Meeting.objects.create(
            id=1,
            meeting_id="id1",
            internal_meeting_id="internalid1",
            meeting_name="Session BBB1",
            encoding_step=0,
        )

        Attendee.objects.create(
            id=1, full_name="John Doe", role="MODERATOR", meeting=meeting1
        )

        User.objects.create(username="pod")
        userJaneDoe = User.objects.create(username="pod2")
        Attendee.objects.create(
            id=2,
            full_name="Jane Doe",
            role="MODERATOR",
            username="pod2",
            meeting=meeting1,
            user=userJaneDoe,
        )

        print(" --->  SetUp of AttendeeTestCase : OK !")

    # Test attributes
    def test_attributes(self):
        attendee = Attendee.objects.get(id=1)
        meeting = Meeting.objects.get(id=1)
        self.assertEqual(attendee.full_name, "John Doe")
        self.assertEqual(attendee.role, "MODERATOR")
        self.assertEqual(attendee.meeting, meeting)

        userJaneDoe = User.objects.get(username="pod2")
        attendee2 = Attendee.objects.get(id=2)
        self.assertEqual(attendee2.full_name, "Jane Doe")
        self.assertEqual(attendee2.role, "MODERATOR")
        self.assertEqual(attendee2.meeting, meeting)
        self.assertEqual(attendee2.username, "pod2")
        self.assertEqual(attendee2.user, userJaneDoe)
        print("   --->  test_attributs of AttendeeTestCase : OK !")

    # Test update attributes
    def test_update_attributes(self):
        attendee = Attendee.objects.get(id=1)
        userJohnDoe = User.objects.get(username="pod")
        attendee.username = "pod"
        attendee.user = userJohnDoe
        attendee.save()
        self.assertEqual(attendee.username, "pod")
        self.assertEqual(attendee.user, userJohnDoe)
        print("   --->  test_update_attributes of AttendeeTestCase : OK !")

    # Test delete object
    def test_delete_object(self):
        Attendee.objects.filter(id=1).delete()
        self.assertEquals(Attendee.objects.all().count(), 1)
        Attendee.objects.filter(id=2).delete()
        self.assertEquals(Attendee.objects.all().count(), 0)

        print("   --->  test_delete_object of AttendeeTestCase : OK !")


class LivestreamTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        meeting1 = Meeting.objects.create(
            id=1,
            meeting_id="id1",
            internal_meeting_id="internalid1",
            meeting_name="Session BBB1",
            encoding_step=0,
        )

        user1 = User.objects.create(username="pod")

        Livestream.objects.create(
            id=1, start_date=timezone.now(), meeting=meeting1, user=user1
        )

        print(" --->  SetUp of LivestreamTestCase : OK !")

    # Test attributes
    def test_attributes(self):
        meeting = Meeting.objects.get(id=1)
        user = User.objects.get(username="pod")
        livestream = Livestream.objects.get(id=1)
        self.assertEqual(livestream.status, 0)
        self.assertEqual(livestream.meeting, meeting)
        self.assertEqual(livestream.user, user)
        date = timezone.now()
        self.assertEqual(livestream.start_date.year, date.year)
        self.assertEqual(livestream.start_date.month, date.month)
        self.assertEqual(livestream.start_date.day, date.day)

        print("   --->  test_attributs of LivestreamTestCase : OK !")

    # Test update attributes
    def test_update_attributes(self):
        livestream = Livestream.objects.get(id=1)
        livestream.status = 1
        livestream.download_meeting = 1
        livestream.enable_chat = 1
        livestream.is_restricted = 1
        livestream.redis_hostname = "localhost"
        livestream.redis_port = 6379
        livestream.broadcaster_id = 1
        livestream.save()
        self.assertEqual(livestream.status, 1)
        self.assertEqual(livestream.download_meeting, 1)
        self.assertEqual(livestream.redis_hostname, "localhost")
        self.assertEqual(livestream.redis_port, 6379)
        self.assertEqual(livestream.broadcaster_id, 1)
        print("   --->  test_update_attributes of LivestreamTestCase : OK !")

    # Test delete object
    def test_delete_object(self):
        Livestream.objects.filter(id=1).delete()
        self.assertEquals(Livestream.objects.all().count(), 0)

        print("   --->  test_delete_object of LivestreamTestCase : OK !")
