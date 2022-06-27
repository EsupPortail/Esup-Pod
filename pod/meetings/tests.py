from unicodedata import name
from django.test import TestCase
from pod.meetings.utils import xml_to_json

from pod.meetings.models import Meetings

class MeetingsTests(TestCase):
    
    def test_get_meetings(self):
        """ Test if BigBlueButton's get_meeting method is working or not.
        It should return list of all running meetings right now!. """
        meeting = Meetings().get_meetings()
        print(meeting)

        # If error in getMeetings() will return 'error' value instead of list of meeting rooms
        self.assertTrue(meeting != 'error')

        self.assertTrue(type(meeting) == list)

    def test_create_meeting(self):
        meetingID = Meetings()
        m = Meetings.create(meetingID)
        self.assertTrue(type(m) == Meetings)

    def test_end_meeting(self):
        meetingID = '0026-pod'
        meeting = Meetings.create(meetingID)

        status = Meetings().end_meeting(meeting.meetingID)
        print(status)

    def test_join_existing_meeting(self):
        meetingID = '0026-pod'
        b = Meetings().join_url(meetingID, 'Antoine Leva')
        print(b)

    def test_create_and_join_meeting(self):
        name = 'Info'
        meetingID = '0038-info'
        meeting = Meetings.create(name, meetingID)

        b = Meetings().join_url(meeting.meetingID, 'Moderator', meeting.moderatorPW)
        print(b)
        # It will print a link. join with it and see if it's ok or not!

        b = Meetings().join_url(meeting.meetingID, 'Attendee', meeting.attendeePW)
        print(b)