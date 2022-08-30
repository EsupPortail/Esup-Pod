from django.test import TestCase
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from ..models import Meeting


class MeetingTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username="pod")
        user1 = User.objects.create(username="pod1")
        user2 = User.objects.create(username="pod2")
        Meeting.objects.create(id=1, name="test", owner=user)
        meeting2 = Meeting.objects.create(
            id=2,
            name="test2",
            owner=user,
            attendee_password="1234",
            moderator_password="1234",
            is_restricted=True,
        )
        meeting2.additional_owners.add(user1)
        meeting2.additional_owners.add(user2)

    def test_default_attributs(self):
        meeting1 = Meeting.objects.get(id=1)
        self.assertEqual(meeting1.name, "test")
        meeting_id = "%04d-%s" % (1, slugify(meeting1.name))
        self.assertEqual(meeting1.meeting_id, meeting_id)
        user = User.objects.get(username="pod")
        self.assertEqual(meeting1.owner, user)
        self.assertEqual(meeting1.additional_owners.all().count(), 0)
        self.assertEqual(meeting1.attendee_password, "")
        self.assertEqual(meeting1.moderator_password, "")
        self.assertEqual(meeting1.is_restricted, False)
        self.assertEqual(meeting1.is_running, False)
        print("   --->  test_default_attributs of MeetingTestCase: OK !")

    def test_with_attributs(self):
        meeting2 = Meeting.objects.get(id=2)
        self.assertEqual(meeting2.name, "test2")
        meeting_id = "%04d-%s" % (meeting2.id, slugify(meeting2.name))
        self.assertEqual(meeting2.meeting_id, meeting_id)
        user = User.objects.get(username="pod")
        self.assertEqual(meeting2.owner, user)
        self.assertEqual(meeting2.additional_owners.all().count(), 2)
        self.assertEqual(meeting2.attendee_password, "1234")
        self.assertEqual(meeting2.moderator_password, "1234")
        self.assertEqual(meeting2.is_restricted, True)
        print("   --->  test_with_attributs of MeetingTestCase: OK !")

    def test_change_attributs(self):
        meeting1 = Meeting.objects.get(id=1)
        self.assertEqual(meeting1.name, "test")
        meeting_id = "%04d-%s" % (meeting1.id, slugify(meeting1.name))
        self.assertEqual(meeting1.meeting_id, meeting_id)
        created_at = meeting1.created_at
        updated_at = meeting1.updated_at
        meeting1.name = "New Test !"
        meeting1.save()
        newmeeting1 = Meeting.objects.get(id=1)
        self.assertEqual(newmeeting1.name, "New Test !")
        self.assertEqual(newmeeting1.get_hashkey(), meeting1.get_hashkey())
        meeting_id = "%04d-%s" % (newmeeting1.id, slugify(newmeeting1.name))
        self.assertEqual(newmeeting1.meeting_id, meeting_id)
        self.assertEqual(created_at, newmeeting1.created_at)
        self.assertNotEqual(updated_at, newmeeting1.updated_at)
        print("   --->  test_change_attributs of MeetingTestCase: OK !")

    def test_delete_object(self):
        Meeting.objects.filter(name="test").delete()
        self.assertEqual(Meeting.objects.all().count(), 1)
        print("   --->  test_delete_object of MeetingTestCase: OK !")
