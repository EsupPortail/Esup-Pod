import http
import json
import logging
import os
import re
import requests

from abc import ABC as __ABC__, abstractmethod
from datetime import timedelta
from typing import Optional
from django.conf import settings

from .models import Broadcaster

__EXISTING_BROADCASTER_IMPLEMENTATIONS__ = ["Wowza"]

DEFAULT_EVENT_PATH = getattr(settings, "DEFAULT_EVENT_PATH", "")

logger = logging.getLogger(__name__)


class PilotingInterface(__ABC__):
    @abstractmethod
    def __init__(self, broadcaster: Broadcaster):
        """Initialize the PilotingInterface
        :param broadcaster: the broadcaster to pilot"""
        self.broadcaster = broadcaster
        raise NotImplementedError

    @abstractmethod
    def check_piloting_conf(self) -> bool:
        """Checks the piloting conf value"""
        raise NotImplementedError

    @abstractmethod
    def is_available_to_record(self) -> bool:
        """Checks if the broadcaster is available"""
        raise NotImplementedError

    @abstractmethod
    def is_recording(self, with_file_check=False) -> bool:
        """Checks if the broadcaster is being recorded
        :param with_file_check:
        checks if tmp recording file is present on the filesystem
        (recording could have been launch from somewhere else)
        """
        raise NotImplementedError

    @abstractmethod
    def start(self, event_id, login=None) -> bool:
        """Start the recording"""
        raise NotImplementedError

    @abstractmethod
    def split(self) -> bool:
        """Split the current record"""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> bool:
        """Stop the recording"""
        raise NotImplementedError

    @abstractmethod
    def get_info_current_record(self) -> dict:
        """Get info of current record"""
        raise NotImplementedError

    @abstractmethod
    def copy_file_to_pod_dir(self, filename) -> bool:
        """Copy the file from remote server to pod server"""
        raise NotImplementedError


def get_piloting_implementation(broadcaster) -> Optional[PilotingInterface]:
    logger.debug("get_piloting_implementation")
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

    logger.warning("->get_piloting_implementation - This should not happen.")
    return None


def is_recording_launched_by_pod(self) -> bool:
    # Récupération du fichier associé à l'enregistrement
    current_record_info = self.get_info_current_record()
    if not current_record_info.get("currentFile"):
        logger.error(" ... impossible to get recording file name")
        return False

    filename = current_record_info.get("currentFile")
    full_file_name = os.path.join(DEFAULT_EVENT_PATH, filename)

    # Vérification qu'il existe bien pour cette instance ce Pod
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

    def check_piloting_conf(self) -> bool:
        logger.debug("Wowza - Check piloting conf")
        conf = self.broadcaster.piloting_conf
        if not conf:
            logger.error(
                "'piloting_conf' value is not set for '"
                + self.broadcaster.name
                + "' broadcaster."
            )
            return False
        try:
            decoded = json.loads(conf)
        except Exception:
            logger.error(
                "'piloting_conf' has not a valid Json format for '"
                + self.broadcaster.name
                + "' broadcaster."
            )
            return False
        if not {"server_url", "application", "livestream"} <= decoded.keys():
            logger.error(
                "'piloting_conf' format value for '"
                + self.broadcaster.name
                + "' broadcaster must be like: "
                "{'server_url':'...','application':'...','livestream':'...'}"
            )
            return False

        logger.debug("->piloting conf OK")
        return True

    def is_available_to_record(self) -> bool:
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

    def start(self, event_id=None, login=None) -> bool:
        logger.debug("Wowza - Start record")
        json_conf = self.broadcaster.piloting_conf
        conf = json.loads(json_conf)
        url_start_record = (
            self.url + "/instances/_definst_/streamrecorders/" + conf["livestream"]
        )
        filename = self.broadcaster.slug
        if event_id is not None:
            filename = str(event_id) + "_" + filename
        elif login is not None:
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

    def split(self) -> bool:
        """Split the recording."""
        return self.execute_action("splitRecording")

    def stop(self) -> bool:
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
            ending = current_file.split("_")[-1]
            if re.match(r"\d+\.", ending):
                number = ending.split(".")[0]
                if int(number) > 0:
                    segment_number = number
        except Exception:
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
        return False
