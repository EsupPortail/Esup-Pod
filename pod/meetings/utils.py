from hashlib import sha1
import logging
import random
from django.conf import settings

import requests
import urllib
import xml.etree.ElementTree as ET

from pod.settings import BBB_API_URL

BBB_CALLBACK_URL = getattr(settings, 'BBB_CALLBACK_URL', None)

UPDATE_RUNNING_ON_EACH_CALL = getattr(settings, 'UPDATE_RUNNING_ON_EACH_CALL', True)

""" Other default variables for each meeting """
BBB_MAX_PARTICIPANTS = getattr(settings, 'BBB_MAX_PARTICIPANTS', 10)
BBB_WELCOME_TEXT = getattr(settings, 'BBB_WELCOME_TEXT', 'Welcome to meeting')
BBB_LOGOUT_URL = getattr(settings, 'BBB_LOGOUT_URL', BBB_API_URL)
BBB_RECORD = getattr(settings, 'BBB_RECORD', True)
BBB_AUTO_RECORDING = getattr(settings, 'BBB_AUTO_RECORDING', False)
BBB_ALLOW_START_STOP_RECORDING = getattr(settings, 'BBB_ALLOW_START_STOP_RECORDING', True)
BBB_WEBCAM_ONLY_FOR_MODS = getattr(settings, 'BBB_WEBCAM_ONLY_FOR_MODS', False)
BBB_LOCK_SETTINGS_DISABLE_CAM = getattr(settings, 'BBB_LOCK_SETTINGS_DISABLE_CAM', False)
BBB_LOCK_SETTINGS_DISABLE_MIC = getattr(settings, 'BBB_LOCK_SETTINGS_DISABLE_MIC', False)
BBB_LOCK_SETTINGS_DISABLE_PRIVATE_CHAT = getattr(settings, 'BBB_LOCK_SETTINGS_DISABLE_PRIVATE_CHAT', False)
BBB_LOCK_SETTINGS_DISABLE_PUBLIC_CHAT = getattr(settings, 'BBB_LOCK_SETTINGS_DISABLE_PUBLIC_CHAT', False)
BBB_LOCK_SETTINGS_DISABLE_NOTE = getattr(settings, 'BBB_LOCK_SETTINGS_DISABLE_NOTE', False)
BBB_LOCK_SETTINGS_LOCKED_LAYOUT = getattr(settings, 'BBB_LOCK_SETTINGS_LOCKED_LAYOUT', False)
BBB_COPYRIGHT_TEXT = getattr(settings, 'BBB_COPYRIGHT_TEXT', 'Copyright to Execut3 (CPOL Co)')

def parse_xml(response):
    try:
        xml = ET.XML(response)
        code = xml.find('returncode').text
        if code == 'SUCCESS':
            return xml
        else:
            raise
    except:
        return None

def xml_to_json(xml):
    result = {}
    for x in xml:
        result[x.tag] = x.text
    return result

class BigBlueButton:
    """ Main class for BigBlueButton
    List of methods:
        - api_call
        - is_running
        - end_meeting
        - meeting_info
        - get_meetings
        - join_url
        - start
    """
    secret_key = settings.BBB_SECRET_KEY
    api_url = settings.BBB_API_URL
    attendee_password = 'ap'
    moderator_password = 'mp'

    def api_call(self, query, call):
        """ Method to create valid API query
        to call on BigBlueButton. Because each query
        should have a encrypted checksum based on request Data.
        """
        prepared = '{}{}{}'.format(call, query, self.secret_key)
        checksum = sha1(str(prepared).encode('utf-8')).hexdigest()
        result = "%s&checksum=%s" % (query, checksum)
        return result

    def is_running(self, meeting_id):
        """ Return whether meeting_id is running or not! """
        call = 'isMeetingRunning'
        query = urllib.parse.urlencode((
            ('meetingID', meeting_id),
        ))
        hashed = self.api_call(query, call)
        url = self.api_url + call + '?' + hashed
        result = parse_xml(requests.get(url).content)
        if result:
            return result.find('running').text
        return 'error'

    def end_meeting(self, meeting_id, password):
        """ End meeting,
        Should provide Moderator password as input to make it work!
        """
        call = 'end'
        query = urllib.parse.urlencode((
            ('meetingID', meeting_id),
            ('password', password),
        ))
        hashed = self.api_call(query, call)
        url = self.api_url + call + '?' + hashed
        req = requests.get(url)
        result = parse_xml(req.content)
        if result:
            return True
        return False

    def meeting_info(self, meeting_id, password):
        """ Get information about meeting.
        result includes below data:
            start_time
            end_time
            participant_count
            moderator_count
            attendee_pw
            moderator_pw
        """
        call = 'getMeetingInfo'
        query = urllib.parse.urlencode((
            ('meetingID', meeting_id),
            ('password', password),
        ))
        hashed = self.api_call(query, call)
        url = self.api_url + call + '?' + hashed
        r = parse_xml(requests.get(url).content)
        if r:
            attendee_list = []
            try:
                for a in r.findall('attendees'):
                    try:
                        x = a.find('attendee')
                        user_id = x.find('userID').text
                        if not user_id:
                            continue
                        fullname = x.find('fullName').text
                        role = x.find('role')
                        attendee_list.append({
                            'id': user_id,
                            'fullname': fullname,
                            'role': role
                        })
                    except:
                        continue
            except Exception as e:
                pass

            # Create dict of values for easy use in template
            d = {
                'start_time': r.find('startTime').text,
                'end_time': r.find('endTime').text,
                'participant_count': r.find('participantCount').text,
                'moderator_count': r.find('moderatorCount').text,
                'moderator_pw': r.find('moderatorPW').text,
                'attendee_pw': r.find('attendeePW').text,
                'attendee_list': attendee_list,
                # 'invite_url': reverse('join', args=[meeting_id]),
            }
            return d
        return None

    def get_meetings(self):
        """ Will return list of running meetings. """
        call = 'getMeetings'
        query = urllib.parse.urlencode((
            ('random', 'random'),
        ))
        hashed = self.api_call(query, call)
        url = self.api_url + call + '?' + hashed
        result = parse_xml(requests.get(url).content)
        # Create dict of values for easy use in template
        d = []
        if result:
            r = result[1].findall('meeting')
            for m in r:
                meeting_id = m.find('meetingID').text
                password = m.find('moderatorPW').text
                d.append({
                    'meeting_id': meeting_id,
                    'running': m.find('running').text,
                    'moderator_pw': password,
                    'attendee_pw': m.find('attendeePW').text,
                    'info': self.meeting_info(
                        meeting_id,
                        password
                    )
                })
        return d

    def join_url(self, meeting_id, name, password, **kwargs):
        """ Join existing meeting_id.
        can send userID also as **kwargs so it will be set on
        meeting join, and can track useful info about users later.
        """
        call = 'join'
        data = (
            ('fullName', name),
            ('meetingID', meeting_id),
            ('password', password),
        )
        for key, value in kwargs.items():
            # Iterate on kwargs keys, and set their key=value in request.
            data = data + ((key, value), )

        query = urllib.parse.urlencode(data)
        hashed = self.api_call(query, call)
        url = self.api_url + call + '?' + hashed
        return url

    def start(self, titre, meeting_id, **kwargs):
        """ Start meeting with provided info.
        Most of BigBlueButton info is provided now.
        TODO: will add more configs for bigbluebutton later!
        """
        call = 'create'
        attendee_password = kwargs.get("attendee_password", self.attendee_password)
        moderator_password = kwargs.get("moderator_password", self.moderator_password)

        # Get extra configs or set default values
        welcome = kwargs.get('welcome_text', ('Welcome!'))
        record = kwargs.get('record', BBB_RECORD)
        auto_start_recording = kwargs.get('auto_start_recording', BBB_AUTO_RECORDING)
        allow_start_stop_recording = kwargs.get('allow_start_stop_recording', BBB_ALLOW_START_STOP_RECORDING)
        logout_url = kwargs.get('logout_url', BBB_LOGOUT_URL)
        webcam_only_for_moderators = kwargs.get('webcam_only_for_moderators', BBB_WEBCAM_ONLY_FOR_MODS)
        voice_bridge = 70000 + random.randint(0, 9999)

        # Making the query string
        query = urllib.parse.urlencode((
            ('titre', titre),
            ('meetingID', meeting_id),
            ('attendeePW', attendee_password),
            ('moderatorPW', moderator_password),
            ('record', record),
            ('welcome', welcome),
            ('bannerText', welcome),
            ('copyright', BBB_COPYRIGHT_TEXT),
            ('logoutURL', logout_url),
            ('voiceBridge', voice_bridge),
            ('autoStartRecording', auto_start_recording),
            ('allowStartStopRecording', allow_start_stop_recording),
            ('webcamsOnlyForModerator', webcam_only_for_moderators),
        ))
        hashed = self.api_call(query, call)
        url = self.api_url + call + '?' + hashed
        result = parse_xml(requests.get(url).content.decode('utf-8'))
        if result:
            return result
        else:
            raise

    # Recordings
    def get_meeting_records(self, meeting_id):
        """ Will return list of records for provided meeting_id """
        try:
            call = 'getRecordings'
            query = urllib.parse.urlencode((
                ('meetingID', meeting_id),
            ))
            hashed = self.api_call(query, call)
            url = self.api_url + call + '?' + hashed
            content = requests.get(url).content
            result = parse_xml(content)
            print(result)
            # Create dict of values for easy use in template
            d = []
            if result:
                r = result[1].findall('recording')
                for m in r:
                    try:
                        record_id = m.find('recordID').text
                        meeting_id = m.find('meetingID').text
                        name = m.find('name').text
                        start_time = m.find('startTime').text
                        end_time = m.find('endTime').text
                        raw_size = m.find('rawSize').text
                        try:
                            url = m.find('playback').find('format').find('url').text
                        except:
                            url = ''
                        d.append({
                            'url': url,
                            'name': name,
                            'end_time': end_time,
                            'raw_size': raw_size,
                            'record_id': record_id,
                            'meeting_id': meeting_id,
                            'start_time': start_time,
                        })
                    except Exception as e:
                        logging.error(str(e))
            return d
        except Exception as e:
            logging.error(str(e))
