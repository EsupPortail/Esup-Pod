"""Tests the models for meeting module."""
import random

from ..models import Meeting, InternalRecording
from datetime import datetime, date
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.template.defaultfilters import slugify
from pod.authentication.models import AccessGroup
from django.utils import timezone


class MeetingTestCase(TestCase):
    """Meetings model tests list.

    Args:
        TestCase (class): test case
    """

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
            start_at=datetime(2022, 6, 27, 14, 0, 0),
            recurring_until=date(2022, 6, 26),
            recurrence="daily",
            owner=user,
        )
        self.assertEqual(meeting.recurring_until, meeting.start)
        m1 = Meeting.objects.create(
            name="a" * 250,
            owner=user,
            attendee_password="1234",
            moderator_password="1234",
        )
        m1.full_clean()  # ok !
        with self.assertRaises(ValidationError) as context:
            m2 = Meeting.objects.create(
                name="a" * 260,
                owner=user,
                attendee_password="1234",
                moderator_password="1234",
            )
            m2.full_clean()
        self.assertEqual(
            context.exception.messages,
            [
                "Ensure this value has at most 250 characters (it has 260).",
                "Ensure this value has at most 255 characters (it has 265).",
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


class OccurencesMeetingTestCase(TestCase):
    """List of tests for the recurring meetings model.

    Args:
        TestCase (class): test case
    """

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

    def test_models_meetings_get_occurrences_no_recurrence(self):
        """A meeting without recurrence should return 1 occurence."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = timezone.make_aware(datetime(2022, 7, 7, 14, 0, 0))
        meeting.recurrence = None
        meeting.save()
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [date(2022, 7, 7)],
        )
        self.assertEqual(
            meeting.get_occurrences(date(2022, 7, 8), date(2050, 1, 1)),
            [],
        )

    def test_models_meetings_get_occurrences_daily_nb_occurrences_filled(self):
        """Daily occurences with date of end of reccurrence filled in but not \
        number of occurrences."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = timezone.make_aware(datetime(2022, 7, 7, 14, 0, 0))
        meeting.recurrence = "daily"
        meeting.frequency = 1
        meeting.recurring_until = date(2022, 8, 2)
        meeting.nb_occurrences = None
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.nb_occurrences, 27)
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [date(2022, 7, i) for i in range(7, 32)]
            + [date(2022, 8, 1), date(2022, 8, 2)],
        )
        # change frequency for daily
        meeting.frequency = 3
        meeting.save()
        meeting.refresh_from_db()
        self.assertEqual(meeting.nb_occurrences, 9)
        # The date of end of recurrence should be corrected
        self.assertEqual(meeting.recurring_until, date(2022, 7, 31))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 7, 7),
                date(2022, 7, 10),
                date(2022, 7, 13),
                date(2022, 7, 16),
                date(2022, 7, 19),
                date(2022, 7, 22),
                date(2022, 7, 25),
                date(2022, 7, 28),
                date(2022, 7, 31),
            ],
        )

    def test_models_meetings_get_occurrences_daily_reset_recurring_until(self):
        """Daily occurences with date of end of reccurrence not leaving any \
        possibliity of repeated occurence."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = timezone.make_aware(datetime(2022, 7, 7, 14, 0, 0))
        meeting.recurrence = "daily"
        meeting.frequency = 3
        meeting.recurring_until = date(2022, 7, 9)
        meeting.nb_occurrences = None
        meeting.save()
        meeting.refresh_from_db()

        self.assertIsNone(meeting.recurrence)
        self.assertEqual(meeting.nb_occurrences, 1)
        self.assertEqual(meeting.recurring_until, meeting.start)
        self.assertEqual(meeting.weekdays, "3")
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [date(2022, 7, 7)],
        )

    def test_models_meetings_get_occurrences_daily_recurring_until_filled(self):
        """Daily occurences with number of occurences filled in but not date of \
        end of occurence. The date of end of reccurrence shoud be calculated if \
        the number of occurrences is repeated."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = timezone.make_aware(datetime(2022, 7, 7, 14, 0, 0))
        meeting.recurrence = "daily"
        meeting.frequency = 1
        meeting.recurring_until = None
        meeting.nb_occurrences = 6
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2022, 7, 12))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 7, 7),
                date(2022, 7, 8),
                date(2022, 7, 9),
                date(2022, 7, 10),
                date(2022, 7, 11),
                date(2022, 7, 12),
            ],
        )
        """
        if you change frequency, you have to pass recurring_util to None to
         re-calculate it again
        """
        meeting.frequency = 3
        meeting.recurring_until = None
        meeting.nb_occurrences = 6
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2022, 7, 22))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 7, 7),
                date(2022, 7, 10),
                date(2022, 7, 13),
                date(2022, 7, 16),
                date(2022, 7, 19),
                date(2022, 7, 22),
            ],
        )
        """
        Daily occurences with number of occurrences less or equal to 1, should lead to
        resettings reccurrence.
        """
        meeting.frequency = 3
        meeting.recurring_until = None
        meeting.nb_occurrences = random.choice([0, 1])
        meeting.save()
        meeting.refresh_from_db()

        self.assertIsNone(meeting.recurrence)
        self.assertEqual(meeting.nb_occurrences, 1)
        self.assertEqual(meeting.recurring_until, meeting.start)
        self.assertEqual(meeting.weekdays, "3")
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [date(2022, 7, 7)],
        )

    # Weekly

    def test_models_meetings_get_occurrences_weekly_null_weekdays_is_reset(self):
        """Weekly recurrence should set weekdays or it is not really a recurrence \
        and should be reset."""
        user = User.objects.get(username="pod")
        meeting = Meeting.objects.create(name="test", owner=user, recurrence="weekly")
        self.assertIsNone(meeting.recurrence)

    def test_models_meetings_get_occurrences_weekly_weekdays_include_start(self):
        """For weekly recurrence, the weekday of the start date should be included \
        in weekdays."""
        meeting = Meeting.objects.get(id=1)
        with self.assertRaises(ValidationError) as context:
            # 2022-7-7 is a Thursday, and weekday 2 is not Tuesday
            meeting.start_at = timezone.make_aware(datetime(2022, 7, 7, 14, 0, 0))
            meeting.recurrence = "weekly"
            meeting.weekdays = "2"
            meeting.save()
        self.assertTrue("weekdays" in context.exception.message_dict)

    def test_models_meetings_get_occurrences_weekly_recurring_until_filled(self):
        """Weekly occurences with date of end of reccurrence filled in but not \
        number of occurrences."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = timezone.make_aware(datetime(2022, 7, 7, 14, 0, 0))
        meeting.recurrence = "weekly"
        meeting.frequency = 1
        meeting.recurring_until = date(2022, 8, 2)
        meeting.nb_occurrences = None
        meeting.weekdays = "135"
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.nb_occurrences, 12)
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 7, 7),
                date(2022, 7, 9),
                date(2022, 7, 12),
                date(2022, 7, 14),
                date(2022, 7, 16),
                date(2022, 7, 19),
                date(2022, 7, 21),
                date(2022, 7, 23),
                date(2022, 7, 26),
                date(2022, 7, 28),
                date(2022, 7, 30),
                date(2022, 8, 2),
            ],
        )
        self.assertEqual(
            meeting.get_occurrences(date(2022, 7, 24), date(2022, 7, 29)),
            [
                date(2022, 7, 26),
                date(2022, 7, 28),
            ],
        )

        meeting.frequency = 3
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.nb_occurrences, 5)
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 7, 7),
                date(2022, 7, 9),
                date(2022, 7, 26),
                date(2022, 7, 28),
                date(2022, 7, 30),
            ],
        )

    def test_models_meetings_get_occurrences_weekly_nb_occurrences_filled(self):
        """Weekly occurences with number of occurrences filled in but not date \
        of end of reccurrence."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = timezone.make_aware(datetime(2022, 7, 6, 14, 0, 0))
        meeting.recurrence = "weekly"
        meeting.frequency = 1
        meeting.recurring_until = None
        meeting.nb_occurrences = 12
        meeting.weekdays = "26"
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2022, 8, 14))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 7, 6),
                date(2022, 7, 10),
                date(2022, 7, 13),
                date(2022, 7, 17),
                date(2022, 7, 20),
                date(2022, 7, 24),
                date(2022, 7, 27),
                date(2022, 7, 31),
                date(2022, 8, 3),
                date(2022, 8, 7),
                date(2022, 8, 10),
                date(2022, 8, 14),
            ],
        )

        meeting.frequency = 3
        meeting.recurring_until = None
        meeting.nb_occurrences = 3
        meeting.weekdays = "26"
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2022, 7, 27))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [date(2022, 7, 6), date(2022, 7, 10), date(2022, 7, 27)],
        )
        self.assertEqual(
            meeting.get_occurrences(date(2022, 7, 7), date(2022, 7, 26)),
            [date(2022, 7, 10)],
        )

    def test_models_meetings_get_occurrences_weekly_reset_weekdays(self):
        """reset weekdays if recurrence not equal to weekly"""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = timezone.make_aware(datetime(2022, 7, 6, 14, 0, 0))
        meeting.recurrence = "weekly"
        meeting.frequency = 1
        meeting.recurring_until = None
        meeting.nb_occurrences = 12
        meeting.weekdays = "26"
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.weekdays, "26")
        meeting.recurrence = "daily"
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.weekdays, None)
        meeting.recurrence = "weekly"
        meeting.weekdays = "126"
        meeting.save()
        meeting.refresh_from_db()
        self.assertEqual(meeting.weekdays, "126")

    def test_models_meetings_get_occurrences_weekly_on_monday(self):
        """check a recurring meeting each monday"""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = timezone.make_aware(datetime(2023, 9, 18, 10, 0, 0))
        meeting.recurrence = "weekly"
        meeting.frequency = 1
        meeting.recurring_until = None
        meeting.nb_occurrences = 12
        meeting.weekdays = "0"  # on monday
        meeting.save()
        meeting.refresh_from_db()
        occurrences = meeting.get_occurrences(meeting.start, meeting.recurring_until)
        self.assertEqual(len(occurrences), 12)
        next_occurrence = meeting.next_occurrence(meeting.start)
        self.assertEqual(next_occurrence, date(2023, 9, 25))
        self.assertEqual(next_occurrence.weekday(), 0)

    # Monthly

    def test_models_meetings_get_occurrences_monthly_nb_occurrences_filled_date(self):
        """Monthly occurences with date of end of recurrence filled in but not number of \
        occurences. The monthly reccurence is on the precise date each month"""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = datetime(2022, 10, 7, 14, 0, 0)
        meeting.recurrence = "monthly"
        meeting.frequency = 1
        meeting.recurring_until = date(2023, 4, 2)
        meeting.nb_occurrences = None
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.nb_occurrences, 6)
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 7),
                date(2022, 11, 7),
                date(2022, 12, 7),
                date(2023, 1, 7),
                date(2023, 2, 7),
                date(2023, 3, 7),
            ],
        )

        meeting.frequency = 3
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.nb_occurrences, 2)
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [date(2022, 10, 7), date(2023, 1, 7)],
        )

    def test_models_meetings_get_occurrences_monthly_recurring_until_filled_date(self):
        """Monthly occurences with number of occurrences filled in but not date of end \
        of reccurrence. The monthly reccurence is on the nth weekday of the month."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = datetime(2022, 10, 7, 14, 0, 0)
        meeting.recurrence = "monthly"
        meeting.frequency = 1
        meeting.recurring_until = None
        meeting.nb_occurrences = 6
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2023, 3, 7))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 7),
                date(2022, 11, 7),
                date(2022, 12, 7),
                date(2023, 1, 7),
                date(2023, 2, 7),
                date(2023, 3, 7),
            ],
        )

        meeting.frequency = 3
        meeting.recurring_until = None
        meeting.nb_occurrences = 8
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2024, 7, 7))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 7),
                date(2023, 1, 7),
                date(2023, 4, 7),
                date(2023, 7, 7),
                date(2023, 10, 7),
                date(2024, 1, 7),
                date(2024, 4, 7),
                date(2024, 7, 7),
            ],
        )

    def test_models_meetings_get_occurrences_monthly_nb_occurrences_filled_nth(self):
        """Monthly occurences with date of end of recurrence filled in but not number \
        of occurences. The monthly reccurence is on the nth weekday of the month."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = datetime(2022, 10, 21, 14, 0, 0)
        meeting.recurrence = "monthly"
        meeting.frequency = 1
        meeting.recurring_until = date(2023, 4, 2)
        meeting.monthly_type = "nth_day"
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.nb_occurrences, 6)
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 21),
                date(2022, 11, 18),
                date(2022, 12, 16),
                date(2023, 1, 20),
                date(2023, 2, 17),
                date(2023, 3, 17),
            ],
        )

        meeting.frequency = 3
        meeting.recurring_until = date(2023, 5, 2)
        meeting.monthly_type = "nth_day"
        meeting.nb_occurrences = None
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.nb_occurrences, 3)
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 21),
                date(2023, 1, 20),
                date(2023, 4, 21),
            ],
        )

    def test_models_meetings_get_occurrences_monthly_recurring_until_filled_nth(self):
        """Monthly occurences with date of end of recurrence filled in but not number \
        of occurrences. The monthly reccurence is on the nth weekday of the month."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = datetime(2022, 10, 21, 14, 0, 0)
        meeting.recurrence = "monthly"
        meeting.frequency = 1
        meeting.recurring_until = None
        meeting.nb_occurrences = 12
        meeting.monthly_type = "nth_day"
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2023, 9, 15))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 21),
                date(2022, 11, 18),
                date(2022, 12, 16),
                date(2023, 1, 20),
                date(2023, 2, 17),
                date(2023, 3, 17),
                date(2023, 4, 21),
                date(2023, 5, 19),
                date(2023, 6, 16),
                date(2023, 7, 21),
                date(2023, 8, 18),
                date(2023, 9, 15),
            ],
        )

        meeting.frequency = 3
        meeting.recurring_until = None
        meeting.nb_occurrences = 8
        meeting.monthly_type = "nth_day"
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2024, 7, 19))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 21),
                date(2023, 1, 20),
                date(2023, 4, 21),
                date(2023, 7, 21),
                date(2023, 10, 20),
                date(2024, 1, 19),
                date(2024, 4, 19),
                date(2024, 7, 19),
            ],
        )

    # Yearly

    def test_models_meetings_get_occurrences_yearly_nb_occurrences_filled(self):
        """Yearly occurences with date of end of recurrence filled in but not \
        number of occurrences."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = datetime(2022, 10, 7, 14, 0, 0)
        meeting.recurrence = "yearly"
        meeting.frequency = 1
        meeting.recurring_until = date(2028, 4, 2)
        meeting.nb_occurrences = None
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.nb_occurrences, 6)
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 7),
                date(2023, 10, 7),
                date(2024, 10, 7),
                date(2025, 10, 7),
                date(2026, 10, 7),
                date(2027, 10, 7),
            ],
        )

        meeting.frequency = 3
        meeting.recurring_until = date(2028, 4, 2)
        meeting.nb_occurrences = None
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.nb_occurrences, 2)
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 7),
                date(2025, 10, 7),
            ],
        )

    def test_models_meetings_get_occurrences_yearly_recurring_until_filled(self):
        """Yearly occurences with number of occurrences filled in but not date of \
        end of reccurrence."""
        meeting = Meeting.objects.get(id=1)
        meeting.start_at = datetime(2022, 10, 7, 14, 0, 0)
        meeting.recurrence = "yearly"
        meeting.frequency = 1
        meeting.recurring_until = None
        meeting.nb_occurrences = 6
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2027, 10, 7))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 7),
                date(2023, 10, 7),
                date(2024, 10, 7),
                date(2025, 10, 7),
                date(2026, 10, 7),
                date(2027, 10, 7),
            ],
        )

        meeting.frequency = 3
        meeting.recurring_until = None
        meeting.nb_occurrences = 8
        meeting.save()
        meeting.refresh_from_db()

        self.assertEqual(meeting.recurring_until, date(2043, 10, 7))
        self.assertEqual(
            meeting.get_occurrences(date(2020, 3, 15), date(2050, 1, 1)),
            [
                date(2022, 10, 7),
                date(2025, 10, 7),
                date(2028, 10, 7),
                date(2031, 10, 7),
                date(2034, 10, 7),
                date(2037, 10, 7),
                date(2040, 10, 7),
                date(2043, 10, 7),
            ],
        )


class InternalRecordingTestCase(TestCase):
    """List of recordings model tests, only internal.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        """Setup for the recordings."""
        user = User.objects.create(username="pod")
        user1 = User.objects.create(username="pod1")
        user2 = User.objects.create(username="pod2")
        meeting1 = Meeting.objects.create(id=1, name="test meeting", owner=user)
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
        InternalRecording.objects.create(
            id=1,
            name="test recording1",
            owner=user,
            recording_id="c057c39d3dc59d9e9516d95f76eb",
            meeting=meeting1,
            site=Site.objects.get(id=1),
        )
        InternalRecording.objects.create(
            id=2,
            name="test recording2",
            owner=user,
            recording_id="d058c39d3dc59d9e9516d95f76eb",
            meeting=meeting2,
            start_at=datetime(2022, 4, 24, 14, 0, 0),
            uploaded_to_pod_by=user2,
            site=Site.objects.get(id=1),
        )

    def test_default_attributs(self):
        """Check all default attributs values when creating a recording."""
        recordings = InternalRecording.objects.all()
        self.assertGreaterEqual(
            recordings[0].start_at.date(), recordings[1].start_at.date()
        )

    def test_with_attributs(self):
        """Check all attributs values passed when creating a recording."""
        meeting2 = Meeting.objects.get(id=2)
        recording2 = InternalRecording.objects.get(id=2)
        self.assertEqual(recording2.name, "test recording2")
        user2 = User.objects.get(username="pod2")
        self.assertEqual(recording2.uploaded_to_pod_by, user2)
        self.assertEqual(recording2.meeting, meeting2)

    def test_change_attributs(self):
        """Change attributs values in a recording and save it."""
        recording1 = InternalRecording.objects.get(id=1)
        self.assertEqual(recording1.name, "test recording1")
        self.assertEqual(recording1.recording_id, "c057c39d3dc59d9e9516d95f76eb")
        recording1.name = "New test recording1 !"
        recording1.recording_id = "d058c39d3dc59d9e9516d95f76eb"
        recording1.save()
        newrecording1 = InternalRecording.objects.get(id=1)
        self.assertEqual(newrecording1.name, "New test recording1 !")
        self.assertEqual(newrecording1.recording_id, "d058c39d3dc59d9e9516d95f76eb")

    def test_delete_object(self):
        """Delete a recording."""
        InternalRecording.objects.filter(name="test recording2").delete()
        self.assertEqual(InternalRecording.objects.all().count(), 1)
