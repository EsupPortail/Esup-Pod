from django.test import TestCase
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from datetime import date
from django.core.exceptions import ValidationError
from ..models import Meeting
from pod.authentication.models import AccessGroup


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
        """Check all default attributs values when creating a meeting"""
        meetings = Meeting.objects.all()
        self.assertGreaterEqual(meetings[0].start, meetings[1].start)
        self.assertGreaterEqual(meetings[0].start_time, meetings[1].start_time)
        """
        The start date can not be greater than the date of end of recurrence.
        """
        user = User.objects.get(username="pod")
        meeting = Meeting.objects.create(
            start=date(2022, 6, 27),
            recurring_until=date(2022, 6, 26),
            recurrence="daily",
            owner=user
        )
        self.assertEqual(meeting.recurring_until, meeting.start)
        m1 = Meeting.objects.create(
            name="a" * 255,
            owner=user,
            attendee_password="1234",
            moderator_password="1234"
        )
        m1.full_clean()  # ok !
        with self.assertRaises(ValidationError) as context:
            m2 = Meeting.objects.create(
                name="a" * 260,
                owner=user,
                attendee_password="1234",
                moderator_password="1234"
            )
            m2.full_clean()
        self.assertEqual(
            context.exception.messages,
            [
                'Ensure this value has at most 255 characters (it has 260).',
                'Ensure this value has at most 260 characters (it has 265).'
            ],
        )

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

    def test_with_attributs(self):
        """Check all attributs values passed when creating a meeting"""
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

    def test_change_attributs(self):
        """Change attributs values in a meeting and save it"""
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

    def test_meetings_additional_owners(self):
        """Add additional_owners to a meeting."""
        meeting = Meeting.objects.get(id=1)
        user = User.objects.get(username="pod")
        meeting.additional_owners.add(user)
        meeting.refresh_from_db()
        self.assertEqual(list(meeting.additional_owners.all()), [user])

    def test_meetings_accessgroup(self):
        """Add AccessGroup to a meeting."""
        meeting = Meeting.objects.get(id=1)
        accessgroup = AccessGroup.objects.create(code_name="ag1")
        meeting.restrict_access_to_groups.add(accessgroup)
        meeting.refresh_from_db()
        self.assertEqual(list(meeting.restrict_access_to_groups.all()), [accessgroup])

    def test_delete_object(self):
        """Delete a meeting."""
        Meeting.objects.filter(name="test").delete()
        self.assertEqual(Meeting.objects.all().count(), 1)
