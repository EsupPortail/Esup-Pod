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
        """ Will try to create a meeting with bbb.
        Example output as json from bbb 'create' command:
        {'returncode': 'SUCCESS', 'meetingID': 'test',
        'internalMeetingID': 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3-1598891360456',
        'parentMeetingID': 'bbb-none', 'attendeePW': 'ap', 'moderatorPW': 'mp',
        'createTime': '1598891360456', 'voiceBridge': '73362', 'dialNumber': '613-555-1234',
        'createDate': 'Mon Aug 31 12:29:20 EDT 2020', 'hasUserJoined': 'false',
        'duration': '0', 'hasBeenForciblyEnded': 'false', 'messageKey': None, 'message': None}
        """
        meeting_name = 'test'
        meeting_id = 'test'

        # First step is to request BBB and create a meeting
        m_xml = Meetings().create(
            name=meeting_name,
            meeting_id=meeting_id,
        )
        meeting_json = xml_to_json(m_xml)
        self.assertTrue(meeting_json['returncode'] == 'SUCCESS')
        self.assertTrue(meeting_json['meetingID'] == meeting_id)

        # Now create a model for it.
        current_meetings = Meetings.objects.count()
        meeting, _ = Meetings.objects.get_or_create(meeting_id=meeting_json['meetingID'])
        meeting.meeting_id = meeting_json['meetingID']
        meeting.name = meeting_name
        meeting.welcome_text = meeting_json['meetingID']
        meeting.attendee_password = meeting_json['attendeePW']
        meeting.moderator_password = meeting_json['moderatorPW']
        meeting.internal_meeting_id = meeting_json['internalMeetingID']
        meeting.parent_meeting_id = meeting_json['parentMeetingID']
        meeting.voice_bridge = meeting_json['voiceBridge']
        meeting.save()

        self.assertFalse(Meetings.objects.count() == current_meetings)

    def test_end_meeting(self):
        name = 'pod'
        meeting = Meetings.create(name)

        status = Meetings().end_meeting(meeting.name)
        print(status)

    def test_join_existing_meeting(self):
        name = 'Antoine Leva'
        meetingID = '0026-pod'
        password = 'pod'
        b = Meetings().join_url(name, meetingID, password)
        print(b)