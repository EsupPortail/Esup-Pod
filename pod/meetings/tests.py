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

    '''
    def test_create_meeting(self):
        name = 'test'
        meetingID = 'test'

        # First step is to request BBB and create a meeting
        m_xml = Meetings.objects.create(
            name="pod",
            meetingID="0007 - pod",
        )
        meeting_json = xml_to_json(m_xml)
        self.assertTrue(meeting_json['returncode'] == 'SUCCESS')
        self.assertTrue(meeting_json['meetingID'] == meetingID)

        # Now create a model for it.
        current_meetings = Meetings.objects.count()
        meeting, _ = Meetings.objects.get_or_create(meetingID=meeting_json['meetingID'])
        meeting.meetingID = meeting_json['meetingID']
        meeting.name = name
        meeting.welcome_text = meeting_json['meetingID']
        meeting.attendee_password = meeting_json['attendeePW']
        meeting.moderator_password = meeting_json['moderatorPW']
        meeting.internal_meeting_id = meeting_json['internalMeetingID']
        meeting.parent_meeting_id = meeting_json['parentMeetingID']
        meeting.voice_bridge = meeting_json['voiceBridge']
        meeting.save()

        self.assertFalse(Meetings.objects.count() == current_meetings)
    '''