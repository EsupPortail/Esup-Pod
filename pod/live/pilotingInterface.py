"""Esup-Pod Piloting Interface."""
import http
import json
import logging
import os
import re
from abc import ABC as __ABC__, abstractmethod
from datetime import timedelta
from typing import Optional, List

import paramiko
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponseNotAllowed

from .models import Broadcaster, Event
from .utils import date_string_to_second

DEFAULT_EVENT_PATH = getattr(settings, "DEFAULT_EVENT_PATH", "")

logger = logging.getLogger(__name__)

__EXISTING_BROADCASTER_IMPLEMENTATIONS__ = ["Wowza", "SMP"]

__MANDATORY_PARAMETERS__ = {
    "Wowza": {"server_url", "application", "livestream"},
    "SMP": {
        "server_url",
        "sftp_port",
        "user",
        "password",
        "record_dir_path",
        "rtmp_streamer_id",
    },
}


class PilotingInterface(__ABC__):
    """Class to be implemented for any device (with an Api) we want to control in the event's page."""

    @abstractmethod
    def __init__(self, broadcaster: Broadcaster):
        """
        Initialize the PilotingInterface.

        Args:
            broadcaster(:class:`pod.live.models.Broadcaster`): the broadcaster to pilot
        """
        self.broadcaster = broadcaster
        raise NotImplementedError

    @abstractmethod
    def copy_file_needed(self) -> bool:
        """If the video file needs to be copied from a remote server."""
        raise NotImplementedError

    @abstractmethod
    def can_split(self) -> bool:
        """If the split function can be executed."""
        raise NotImplementedError

    @abstractmethod
    def check_piloting_conf(self) -> bool:
        """Check the piloting conf value."""
        raise NotImplementedError

    @abstractmethod
    def is_available_to_record(self) -> bool:
        """Check if the broadcaster is available."""
        raise NotImplementedError

    @abstractmethod
    def is_recording(self, with_file_check=False) -> bool:
        """
        Check if the broadcaster is recording state.

        Args:
            with_file_check(bool): checks if tmp recording file is present on the
                filesystem, as recording could have been launch from somewhere else.
        Returns:
            bool: True if the broadcaster is recording state
        """
        raise NotImplementedError

    @abstractmethod
    def start_recording(self, event_id, login=None) -> bool:
        """Start the recording."""
        raise NotImplementedError

    @abstractmethod
    def split_recording(self) -> bool:
        """Split the current record."""
        raise NotImplementedError

    @abstractmethod
    def stop_recording(self) -> bool:
        """Stop the recording."""
        raise NotImplementedError

    @abstractmethod
    def get_info_current_record(self) -> dict:
        """Get info of current record."""
        raise NotImplementedError

    @abstractmethod
    def copy_file_to_pod_dir(self, filename) -> bool:
        """Copy the file from remote server to pod server."""
        raise NotImplementedError

    @abstractmethod
    def can_manage_stream(self) -> bool:
        """If the stream can be started and stopped."""
        raise NotImplementedError

    @abstractmethod
    def start_stream(self) -> bool:
        """Start the stream."""
        raise NotImplementedError

    @abstractmethod
    def stop_stream(self) -> bool:
        """Stop the streams."""
        raise NotImplementedError

    @abstractmethod
    def get_stream_rtmp_infos(self) -> dict:
        """Check if SMP is configured for Rtmp and gets infos."""
        raise NotImplementedError


def ajax_get_mandatory_parameters(request):
    """Return the mandatory parameters as a json response."""
    if request.method == "GET" and request.is_ajax():
        impl_name = request.GET.get("impl_name", None)
        params = get_mandatory_parameters(impl_name)
        params_json = {}
        for value in params:
            params_json[value] = "..."

        return JsonResponse(data=params_json)

    return HttpResponseNotAllowed(["GET"])


def get_mandatory_parameters(impl_name="") -> List[str]:
    """Return the mandatory parameters of the implementation."""
    if impl_name in __MANDATORY_PARAMETERS__:
        return __MANDATORY_PARAMETERS__[impl_name]
    if impl_name.lower() in __MANDATORY_PARAMETERS__:
        return __MANDATORY_PARAMETERS__[impl_name.lower()]
    if impl_name.title() in __MANDATORY_PARAMETERS__:
        return __MANDATORY_PARAMETERS__[impl_name.title()]
    if impl_name.upper() in __MANDATORY_PARAMETERS__:
        return __MANDATORY_PARAMETERS__[impl_name.upper()]
    return [""]


def validate_json_implementation(broadcaster: Broadcaster) -> bool:
    """Return if the config value is json formatted and has all mandatory params."""
    conf = broadcaster.piloting_conf
    if not conf:
        logger.error(
            "'piloting_conf' value is not set for '" + broadcaster.name + "' broadcaster."
        )
        return False
    try:
        decoded = json.loads(conf)
    except Exception as e:
        logger.error(
            "'piloting_conf' has not a valid Json format for '"
            + broadcaster.name
            + "' broadcaster. "
            + str(e)
        )
        return False

    parameters = get_mandatory_parameters(broadcaster.piloting_implementation)

    if not parameters <= decoded.keys():
        mandatory = ""
        for value in parameters:
            mandatory += "'" + value + "':'...',"
        logger.error(
            "'piloting_conf' format value for '"
            + broadcaster.name
            + "' broadcaster must be like : "
            + "{"
            + mandatory[:-1]
            + "}"
        )
        return False

    return True


def get_piloting_implementation(broadcaster) -> Optional[PilotingInterface]:
    """Return the class inheriting from PilotingInterface according to the broadcaster configuration (or None)."""
    if broadcaster is None:
        return None

    piloting_impl = broadcaster.piloting_implementation
    if not piloting_impl:
        logger.info(
            "'piloting_implementation' value is not set for '"
            + broadcaster.name
            + "' broadcaster."
        )
        return None

    map_interface = map(str.lower, __EXISTING_BROADCASTER_IMPLEMENTATIONS__)
    if not piloting_impl.lower() in map_interface:
        logger.warning(
            "'piloting_implementation': "
            + piloting_impl
            + " is not know for '"
            + broadcaster.name
            + "' broadcaster. Available piloting_implementations are '"
            + "','".join(__EXISTING_BROADCASTER_IMPLEMENTATIONS__)
            + "'"
        )
        return None

    if piloting_impl.lower() == "wowza":
        logger.debug(
            "'piloting_implementation' found: "
            + piloting_impl.lower()
            + " for '"
            + broadcaster.name
            + "' broadcaster."
        )
        return Wowza(broadcaster)

    if piloting_impl.lower() == "smp":
        logger.debug(
            "piloting_implementation found : '"
            + piloting_impl.lower()
            + "' for broadcaster : '"
            + broadcaster.name
            + "'"
        )
        return Smp(broadcaster)

    logger.warning("->get_piloting_implementation - This should not happen.")
    return None


def is_recording_launched_by_pod(self) -> bool:
    """Return if the current recording has been launched by Pod."""
    # Fetch file name of current recording
    current_record_info = self.get_info_current_record()
    filename = current_record_info.get("currentFile", None)
    if not filename:
        logger.error(" ... impossible to get recording file name")
        return False

    full_file_name = os.path.join(DEFAULT_EVENT_PATH, filename)

    # Check if this file exists in Pod filesystem
    if not os.path.exists(full_file_name):
        logger.debug(" ...  is not on this POD recording filesystem: " + full_file_name)
        return False

    return True


class Wowza(PilotingInterface):
    def __init__(self, broadcaster: Broadcaster):
        self.broadcaster = broadcaster
        self.url = None
        if self.check_piloting_conf():
            conf = json.loads(self.broadcaster.piloting_conf)
            url = "{server_url}/v2/servers/_defaultServer_"
            url += "/vhosts/_defaultVHost_/applications/{application}"
            self.url = url.format(
                server_url=conf["server_url"],
                application=conf["application"],
            )

    def copy_file_needed(self) -> bool:
        """Implement copy_file_needed from PilotingInterface."""
        return False

    def can_split(self) -> bool:
        """Implement can_split from PilotingInterface."""
        return True

    def check_piloting_conf(self) -> bool:
        """Implement check_piloting_conf from PilotingInterface."""
        return validate_json_implementation(self.broadcaster)

    def is_available_to_record(self) -> bool:
        """Implement is_available_to_record from PilotingInterface."""
        logger.debug("Wowza - Check availability")
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_state_live_stream_recording = (
            self.url + "/instances/_definst_/incomingstreams/" + conf["livestream"]
        )

        response = requests.get(
            url_state_live_stream_recording,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

        if response.status_code == http.HTTPStatus.OK:
            if (
                response.json().get("isConnected") is True
                and response.json().get("isRecordingSet") is False
            ):
                return True

        return False

    def is_recording(self, with_file_check=False) -> bool:
        """Implement is_recording from PilotingInterface."""
        logger.debug("Wowza - Check if is being recorded")
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_state_live_stream_recording = (
            self.url + "/instances/_definst_/incomingstreams/" + conf["livestream"]
        )

        response = requests.get(
            url_state_live_stream_recording,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

        if (
            response.status_code != http.HTTPStatus.OK
            or not response.json().get("isConnected")
            or not response.json().get("isRecordingSet")
        ):
            return False

        if with_file_check:
            return is_recording_launched_by_pod(self)
        else:
            return True

    def start_recording(self, event_id, login=None) -> bool:
        """Implement start_recording from PilotingInterface."""
        logger.debug("Wowza - Start record")
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_start_record = (
            self.url + "/instances/_definst_/streamrecorders/" + conf["livestream"]
        )
        filename = str(event_id) + "_" + self.broadcaster.slug
        if login is not None:
            filename = login + "_" + filename
        data = {
            "instanceName": "",
            "fileVersionDelegateName": "",
            "serverName": "",
            "recorderName": "",
            "currentSize": 0,
            "segmentSchedule": "",
            "startOnKeyFrame": True,
            "outputPath": DEFAULT_EVENT_PATH,
            "baseFile": filename + "_${RecordingStartTime}_${SegmentNumber}",
            "currentFile": "",
            "saveFieldList": [""],
            "recordData": False,
            "applicationName": "",
            "moveFirstVideoFrameToZero": False,
            "recorderErrorString": "",
            "segmentSize": 0,
            "defaultRecorder": False,
            "splitOnTcDiscontinuity": False,
            "version": "",
            "segmentDuration": 0,
            "recordingStartTime": "",
            "fileTemplate": "",
            "backBufferTime": 0,
            "segmentationType": "",
            "currentDuration": 0,
            "fileFormat": "",
            "recorderState": "",
            "option": "",
        }

        response = requests.post(
            url_start_record,
            json=data,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

        if response.status_code == http.HTTPStatus.CREATED:
            if response.json().get("success"):
                return True

        return False

    def execute_action(self, action) -> bool:
        """Execute a Wowza action."""
        logger.debug("Wowza - %s" % action)
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_split_record = (
            self.url
            + "/instances/_definst_/streamrecorders/"
            + conf["livestream"]
            + "/actions/%s" % action
        )
        response = requests.put(
            url_split_record,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

        if response.status_code == http.HTTPStatus.OK:
            if response.json().get("success"):
                return True

        return False

    def split_recording(self) -> bool:
        """Split the recording."""
        if self.can_split():
            return self.execute_action("splitRecording")
        return False

    def stop_recording(self) -> bool:
        """Stop the recording."""
        return self.execute_action("stopRecording")

    def get_info_current_record(self):
        """Get information about the current recording."""
        logger.debug("Wowza - Get info from current record")
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_state_live_stream_recording = (
            self.url + "/instances/_definst_/streamrecorders/" + conf["livestream"]
        )

        response = requests.get(
            url_state_live_stream_recording,
            verify=True,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

        if response.status_code != http.HTTPStatus.OK:
            return {
                "currentFile": "",
                "segmentNumber": "",
                "outputPath": "",
                "durationInSeconds": "",
            }

        segment_number = ""
        current_file = response.json().get("currentFile")

        try:
            ending = current_file.split("_")[-1] if current_file else ""
            if re.match(r"\d+\.", ending):
                number = ending.split(".")[0]
                if int(number) > 0:
                    segment_number = number
        except IndexError:
            pass

        segment_duration = response.json().get("segmentDuration", 0)
        elapsed_time = timedelta(milliseconds=int(segment_duration)).total_seconds()
        return {
            "currentFile": current_file,
            "segmentNumber": segment_number,
            "outputPath": response.json().get("outputPath"),
            "durationInSeconds": int(elapsed_time),
        }

    def copy_file_to_pod_dir(self, filename):
        """Implement copy_file_to_pod_dir from PilotingInterface."""
        return False

    def can_manage_stream(self) -> bool:
        """Implement can_manage_stream from PilotingInterface."""
        return False

    def start_stream(self) -> bool:
        """Implement start_stream from PilotingInterface."""
        return False

    def stop_stream(self) -> bool:
        """Implement stop_stream from PilotingInterface."""
        return False

    def get_stream_rtmp_infos(self) -> dict:
        """Implement get_stream_rtmp_infos from PilotingInterface."""
        return {}


class Smp(PilotingInterface):
    def __init__(self, broadcaster: Broadcaster):
        self.broadcaster = broadcaster
        self.url = None
        if self.check_piloting_conf():
            conf = json.loads(self.broadcaster.piloting_conf)
            url = "{server_url}/api/swis/resources"
            self.url = url.format(
                server_url=conf["server_url"],
                # smp_version=conf["smp_version"],
            )

    def copy_file_needed(self) -> bool:
        """Implement copy_file_needed from PilotingInterface."""
        return True

    def can_split(self) -> bool:
        """Implement can_split from PilotingInterface."""
        return False

    def check_piloting_conf(self) -> bool:
        """Implement check_piloting_conf from PilotingInterface."""
        return validate_json_implementation(self.broadcaster)

    def is_available_to_record(self) -> bool:
        """Implement is_available_to_record from PilotingInterface."""
        logger.debug("Smp - Check availability")
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_state_live_stream_recording = self.url + "?uri=/record/state"

        response = requests.get(
            url_state_live_stream_recording,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(conf["user"], conf["password"]),
        )

        return self.verify_smp_response(response, "result", "stopped")

    def is_recording(self, with_file_check=False) -> bool:
        """Implement is_recording from PilotingInterface."""
        logger.debug("Smp - Check if is being recorded")
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_state_live_stream_recording = self.url + "?uri=/record/state"

        response = requests.get(
            url_state_live_stream_recording,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(conf["user"], conf["password"]),
        )

        return self.verify_smp_response(response, "result", "recording")

    def start_recording(self, event_id, login=None) -> bool:
        """Implement start_recording from PilotingInterface."""
        logger.debug("Smp - Start record")
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_stop_record = self.url

        event = Event.objects.filter(id=event_id).first()
        filename = event.slug if event else str(event_id) + "_" + self.broadcaster.slug
        login = login if login else "unknown"
        body = json.dumps(
            [
                {"uri": "/record/1/root_dir_fs", "value": "internal"},
                {
                    "uri": "/record/control",
                    "value": {
                        "recording": "record",
                        "location": "internal",
                        "metadata": {
                            "title": filename,
                            "creator": login,
                            "description": "launch from Pod",
                        },
                    },
                },
            ]
        )
        response = requests.put(
            url_stop_record,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(conf["user"], conf["password"]),
            data=body,
        )
        return self.verify_smp_response(response, "recording", "record")

    def split_recording(self) -> bool:
        """Implement split_recording from PilotingInterface."""
        logger.error("Smp - Split record - should not be called")
        return False

    def stop_recording(self) -> bool:
        """Implement stop_recording from PilotingInterface."""
        logger.debug("Smp - Stop_record")

        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_stop_record = self.url
        response = requests.put(
            url_stop_record,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(conf["user"], conf["password"]),
            data=json.dumps([{"uri": "/record/control", "value": "stop"}]),
        )
        return self.verify_smp_response(response, "result", "stop")

    def get_info_current_record(self):
        """Implement get_info_current_record from PilotingInterface."""
        logger.debug("Smp - Get info from current record")
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_info_live_stream = self.url + "?uri=/record"

        response = requests.get(
            url_info_live_stream,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(conf["user"], conf["password"]),
        )

        if (
            response.status_code != http.HTTPStatus.OK
            or not response.json()
            or response.json()[0].get("result", "") == ""
        ):
            logger.warning("get_info_current_record in error")
            return {
                "currentFile": "",
                "segmentNumber": "",
                "outputPath": "",
                "durationInSeconds": "",
            }

        infos = response.json()[0].get("result")

        return {
            "segmentNumber": "",
            "currentFile": infos.get("filename"),
            "outputPath": infos.get("root_dir_fs"),
            "durationInSeconds": date_string_to_second(infos.get("elapsed_time")),
        }

    def copy_file_to_pod_dir(self, filename):
        """Implement copy_file_to_pod_dir from PilotingInterface."""
        logger.debug("Smp - Copy file to Pod dir")

        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)

        smp_file_dir = conf["record_dir_path"]

        # because filename can be a path
        file_head_tail = os.path.split(filename)
        if file_head_tail[0]:
            smp_file_path = smp_file_dir + filename
        else:
            smp_file_path = os.path.join(smp_file_dir, filename)

        # SFTP Server Credentials
        ftp_host = re.sub("https?://", "", conf["server_url"])
        ftp_user = conf["user"]
        ftp_pwd = conf["password"]
        ftp_port = int(conf["sftp_port"])

        try:
            # connection to SFTP Server
            t = paramiko.Transport((ftp_host, ftp_port))
            t.connect(None, ftp_user, ftp_pwd)
            sftp = paramiko.SFTPClient.from_transport(t)
            logger.debug("-- connection ok ")

            # where the file will be stored
            pod_file_name = file_head_tail[1]
            pod_file_path = os.path.join(DEFAULT_EVENT_PATH, pod_file_name)
            logger.debug(
                "-- try to copy from SMP : "
                + smp_file_path
                + " to Pod : "
                + pod_file_path
            )

            # copy from remote to local
            sftp.get(smp_file_path, pod_file_path)
            logger.debug("-- copied!")

            # close the connection
            logger.debug("-- closing connection")
            sftp.close()
            return True
        except OSError as e:
            logger.error("Failed to copy file over SFTP : " + str(e))
        return False

    def can_manage_stream(self) -> bool:
        """Implement can_manage_stream from PilotingInterface."""
        return True

    def start_stream(self) -> bool:
        """Implement start_stream from PilotingInterface."""
        return self.set_stream_status(1)

    def stop_stream(self) -> bool:
        """Implement stop_stream from PilotingInterface."""
        return self.set_stream_status(0)

    def get_stream_rtmp_infos(self) -> dict:
        """Implement get_stream_rtmp_infos from PilotingInterface."""
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)

        response = requests.get(
            url=f"{self.url}?uri=/streamer/rtmp/{conf['rtmp_streamer_id']}",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(conf["user"], conf["password"]),
        )

        if (
            response.status_code != http.HTTPStatus.OK
            or not response.json()
            or not type(response.json()) is list
        ):
            return {"error": "fail to fetch infos rtmp"}

        # Verify all infos are present in the streamer
        streamer = response.json()[0]
        if (
            streamer.get("result", "")
            and streamer["result"].get("pub_url", "")
            and "pub_control" in streamer["result"]
            and "pub_while_record" in streamer["result"]
            and streamer.get("meta", "")
            and streamer["meta"].get("uri", "")
        ):
            return {
                "streamer_id": int(conf["rtmp_streamer_id"]),
                "auto_start_on_record": bool(streamer["result"]["pub_while_record"]),
                "is_streaming": bool(streamer["result"]["pub_control"]),
            }
        return {}

    def set_stream_status(self, value) -> bool:
        """Set the RTMP stream status and return if successfully done."""
        if not self.can_manage_stream:
            return False

        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        response = requests.put(
            self.url,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(conf["user"], conf["password"]),
            data=json.dumps(
                [
                    {
                        "uri": f"/streamer/rtmp/{conf['rtmp_streamer_id']}/pub_control",
                        "value": value,
                    }
                ]
            ),
        )
        return self.verify_smp_response(response, "result", value)

    @staticmethod
    def verify_smp_response(response: requests.Response, key, value) -> bool:
        """Verify SMP response is Ok and has key and value in it."""
        if response.status_code != http.HTTPStatus.OK:
            return False
        if not response.json():
            return False

        for resp in response.json():
            if resp.get(key, "") == value:
                return True
            for body in resp.values():
                if type(body) is dict and body.get(key, "") == value:
                    return True
        return False
