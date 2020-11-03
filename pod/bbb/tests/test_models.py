
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import Meeting, User as BBBUser


class MeetingTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        Meeting.objects.create(id=1, meeting_id="id1",
                               internal_meeting_id="internalid1",
                               meeting_name="Session BBB1",
                               encoding_step=0)

        user = User.objects.create(username="pod")
        Meeting.objects.create(id=2, meeting_id="id2",
                               internal_meeting_id="internalid2",
                               meeting_name="Session BBB2",
                               encoding_step=1,
                               encoded_by=user)

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
        print(
            "   --->  test_attributs of MeetingTestCase : OK !")

    # Test update attributes
    def test_update_attributes(self):
        meeting = Meeting.objects.get(id=1)
        user = User.objects.get(username="pod")
        meeting.encoding_step = 1
        meeting.encoded_by = user
        meeting.save()
        self.assertEqual(meeting.encoding_step, 1)
        self.assertEqual(meeting.encoded_by, user)
        print(
            "   --->  test_update_attributes of MeetingTestCase : OK !")

    # Test delete object
    def test_delete_object(self):
        Meeting.objects.filter(meeting_id="id1").delete()
        self.assertEquals(Meeting.objects.all().count(), 1)
        Meeting.objects.filter(meeting_id="id2").delete()
        self.assertEquals(Meeting.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of MeetingTestCase : OK !")


class BBBUserTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        meeting1 = Meeting.objects.create(id=1, meeting_id="id1",
                                          internal_meeting_id="internalid1",
                                          meeting_name="Session BBB1",
                                          encoding_step=0)

        BBBUser.objects.create(id=1, full_name="John Doe",
                               role="MODERATOR",
                               meeting=meeting1)

        User.objects.create(username="pod")
        userJaneDoe = User.objects.create(username="pod2")
        BBBUser.objects.create(id=2, full_name="Jane Doe",
                               role="MODERATOR",
                               username="pod2",
                               meeting=meeting1,
                               user=userJaneDoe)

        print(" --->  SetUp of BBBUserTestCase : OK !")

    # Test attributes
    def test_attributes(self):
        bbbUser = BBBUser.objects.get(id=1)
        meeting = Meeting.objects.get(id=1)
        self.assertEqual(bbbUser.full_name, "John Doe")
        self.assertEqual(bbbUser.role, "MODERATOR")
        self.assertEqual(bbbUser.meeting, meeting)

        userJaneDoe = User.objects.get(username="pod2")
        bbbUser2 = BBBUser.objects.get(id=2)
        self.assertEqual(bbbUser2.full_name, "Jane Doe")
        self.assertEqual(bbbUser2.role, "MODERATOR")
        self.assertEqual(bbbUser2.meeting, meeting)
        self.assertEqual(bbbUser2.username, "pod2")
        self.assertEqual(bbbUser2.user, userJaneDoe)
        print(
            "   --->  test_attributs of BBBUserTestCase : OK !")

    # Test update attributes
    def test_update_attributes(self):
        bbbUser = BBBUser.objects.get(id=1)
        userJohnDoe = User.objects.get(username="pod")
        bbbUser.username = "pod"
        bbbUser.user = userJohnDoe
        bbbUser.save()
        self.assertEqual(bbbUser.username, "pod")
        self.assertEqual(bbbUser.user, userJohnDoe)
        print(
            "   --->  test_update_attributes of BBBUserTestCase : OK !")

    # Test delete object
    def test_delete_object(self):
        BBBUser.objects.filter(id=1).delete()
        self.assertEqual(BBBUser.objects.all().count(), 1)
        BBBUser.objects.filter(id=2).delete()
        self.assertEqual(BBBUser.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of BBBUserTestCase : OK !")
