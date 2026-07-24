"""
Esup-Pod - Live piloting service.

Provides the abstract PilotingInterface and concrete implementations
(Wowza, SMP) that communicate with external recording hardware.
Ported from pod/live/pilotingInterface.py (V4) as a clean service layer.

All network calls that may block must be delegated to Celery tasks
when called from an API endpoint (see tasks.py).
"""

import http
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import timedelta

import requests

logger = logging.getLogger(__name__)

# --- Constants ---
CREATE_VIDEO_FROM_FTP = "fetch file from remote using ftp"
CREATE_VIDEO_FROM_FS = "file is in Pod file system"
CREATE_VIDEO_OPENCAST = "file is automatically sent to the recorder module"

EXISTING_IMPLEMENTATIONS = ["Wowza", "SMP"]

MANDATORY_PARAMETERS = {
    "Wowza": {"server_url", "application", "livestream"},
    "SMP": [
        "server_url",
        "sftp_port",
        "user",
        "password",
        "use_opencast",
        "rtmp_streamer_id",
        "record_dir_path",
    ],
}

OPTIONAL_IF_OPENCAST = ["record_dir_path"]


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class PilotingInterface(ABC):
    """Abstract interface for any external device that can record a live stream."""

    @abstractmethod
    def __init__(self, broadcaster):
        """Initialise the piloting implementation for the given broadcaster."""
        self.broadcaster = broadcaster

    @abstractmethod
    def video_creation_method(self) -> str:
        """Return the method used to create the video after recording."""

    @abstractmethod
    def can_split(self) -> bool:
        """Return True if the split-recording function is supported."""

    @abstractmethod
    def check_piloting_conf(self) -> bool:
        """Validate the JSON piloting_conf stored on the Broadcaster."""

    @abstractmethod
    def is_available_to_record(self) -> bool:
        """Return True if the broadcaster is online and free to start recording."""

    @abstractmethod
    def is_recording(self, with_file_check: bool = False) -> bool:
        """Return True if the broadcaster is currently recording."""

    @abstractmethod
    def start_recording(self, event_id: int) -> bool:
        """Send the start-record command to the device."""

    @abstractmethod
    def split_recording(self) -> bool:
        """Split the current recording segment."""

    @abstractmethod
    def stop_recording(self) -> bool:
        """Send the stop-record command to the device."""

    @abstractmethod
    def get_info_current_record(self) -> dict:
        """Return metadata about the current recording (filename, duration, etc.)."""

    @abstractmethod
    def copy_file_to_pod_dir(self, filename: str) -> bool:
        """Copy the recorded file from the remote server to the local Pod filesystem."""

    @abstractmethod
    def can_manage_stream(self) -> bool:
        """Return True if the stream can be started/stopped via this implementation."""

    @abstractmethod
    def start_stream(self) -> bool:
        """Start the RTMP stream."""

    @abstractmethod
    def stop_stream(self) -> bool:
        """Stop the RTMP stream."""

    @abstractmethod
    def get_stream_rtmp_infos(self) -> dict:
        """Return RTMP configuration information."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_mandatory_parameters(impl_name: str) -> set | list:
    """Return the list of required piloting_conf keys for the given implementation."""
    for key in (impl_name, impl_name.lower(), impl_name.title(), impl_name.upper()):
        if key in MANDATORY_PARAMETERS:
            return MANDATORY_PARAMETERS[key]
    return {}


def validate_json_implementation(broadcaster) -> bool:
    """Return True if piloting_conf is valid JSON containing all mandatory parameters."""
    conf_str = broadcaster.piloting_conf
    if not conf_str:
        logger.error("piloting_conf is not set for broadcaster '%s'.", broadcaster.name)
        return False
    try:
        config = json.loads(conf_str)
    except json.JSONDecodeError as exc:
        logger.error(
            "piloting_conf has invalid JSON for broadcaster '%s': %s",
            broadcaster.name,
            exc,
        )
        return False

    required = get_mandatory_parameters(broadcaster.piloting_implementation)
    use_opencast = config.get("use_opencast", "").lower() == "true"
    missing = []
    for param in required:
        if param not in config:
            if use_opencast and param in OPTIONAL_IF_OPENCAST:
                continue
            missing.append(param)

    if missing:
        logger.error(
            "piloting_conf for broadcaster '%s' is missing: %s",
            broadcaster.name,
            ", ".join(missing),
        )
        return False
    return True


def get_piloting_implementation(broadcaster) -> PilotingInterface | None:
    """
    Factory: return the appropriate PilotingInterface subclass for the broadcaster,
    or None if no implementation is configured or recognised.
    """
    if broadcaster is None:
        return None
    impl = broadcaster.piloting_implementation
    if not impl:
        logger.info(
            "No piloting_implementation set for broadcaster '%s'.", broadcaster.name
        )
        return None
    if impl.lower() == "wowza":
        return Wowza(broadcaster)
    if impl.lower() == "smp":
        return Smp(broadcaster)
    logger.warning(
        "Unknown piloting_implementation '%s' for broadcaster '%s'. " "Available: %s",
        impl,
        broadcaster.name,
        ", ".join(EXISTING_IMPLEMENTATIONS),
    )
    return None


def is_recording_launched_by_pod(impl: PilotingInterface) -> bool:
    """Return True if the current recording was started by Pod (file exists on disk)."""
    from src.apps.live.conf import live_settings

    info = impl.get_info_current_record()
    filename = info.get("currentFile")
    if not filename:
        return False
    full_path = os.path.join(live_settings.default_event_path, filename)
    return os.path.exists(full_path)


# ---------------------------------------------------------------------------
# Wowza implementation
# ---------------------------------------------------------------------------


class Wowza(PilotingInterface):
    """Piloting implementation for Wowza Streaming Engine."""

    def __init__(self, broadcaster):
        """Initialise the piloting implementation for the given broadcaster."""
        self.broadcaster = broadcaster
        self.url: str | None = None
        if self.check_piloting_conf():
            conf = json.loads(broadcaster.piloting_conf)
            self.url = (
                "{server_url}/v2/servers/_defaultServer_"
                "/vhosts/_defaultVHost_/applications/{application}"
            ).format(**conf)

    def video_creation_method(self) -> str:
        return CREATE_VIDEO_FROM_FS

    def can_split(self) -> bool:
        return True

    def check_piloting_conf(self) -> bool:
        return validate_json_implementation(self.broadcaster)

    def is_available_to_record(self) -> bool:
        """Check if broadcaster is online and available to record."""
        conf = json.loads(self.broadcaster.piloting_conf)
        url = self.url + f"/instances/_definst_/incomingstreams/{conf['livestream']}"
        try:
            resp = requests.get(url, headers={"Accept": "application/json"}, timeout=5)
        except requests.RequestException as exc:
            logger.warning("Wowza availability check failed: %s", exc)
            return False
        if resp.status_code == http.HTTPStatus.OK:
            data = resp.json()
            return data.get("isConnected") is True and data.get("isRecordingSet") is False
        return False

    def is_recording(self, with_file_check: bool = False) -> bool:
        """Check if the broadcaster is currently recording."""
        conf = json.loads(self.broadcaster.piloting_conf)
        url = self.url + f"/instances/_definst_/incomingstreams/{conf['livestream']}"
        try:
            resp = requests.get(url, headers={"Accept": "application/json"}, timeout=5)
        except requests.RequestException:
            return False
        if resp.status_code != http.HTTPStatus.OK:
            return False
        data = resp.json()
        if not (data.get("isConnected") and data.get("isRecordingSet")):
            return False
        return is_recording_launched_by_pod(self) if with_file_check else True

    def start_recording(self, event_id: int) -> bool:
        """Send start-record command to the Wowza server."""
        from src.apps.live.conf import live_settings

        conf = json.loads(self.broadcaster.piloting_conf)
        url = self.url + f"/instances/_definst_/streamrecorders/{conf['livestream']}"
        filename = f"{event_id}_{self.broadcaster.slug}"
        payload = {
            "startOnKeyFrame": True,
            "outputPath": live_settings.default_event_path,
            "baseFile": filename + "_${RecordingStartTime}_${SegmentNumber}",
            "defaultRecorder": False,
        }
        try:
            resp = requests.post(
                url, json=payload, headers={"Accept": "application/json"}, timeout=10
            )
        except requests.RequestException as exc:
            logger.error("Wowza start_recording failed: %s", exc)
            return False
        return resp.status_code == http.HTTPStatus.CREATED and bool(
            resp.json().get("success")
        )

    def _execute_action(self, action: str) -> bool:
        """Execute a named action (split/stop) on the Wowza stream recorder."""
        conf = json.loads(self.broadcaster.piloting_conf)
        url = (
            self.url
            + f"/instances/_definst_/streamrecorders/{conf['livestream']}/actions/{action}"
        )
        try:
            resp = requests.put(url, headers={"Accept": "application/json"}, timeout=10)
        except requests.RequestException as exc:
            logger.error("Wowza execute_action '%s' failed: %s", action, exc)
            return False
        return resp.status_code == http.HTTPStatus.OK and bool(resp.json().get("success"))

    def split_recording(self) -> bool:
        """Split the current recording segment."""
        return self._execute_action("splitRecording") if self.can_split() else False

    def stop_recording(self) -> bool:
        """Send stop-record command to the device."""
        return self._execute_action("stopRecording")

    def get_info_current_record(self) -> dict:
        """Return metadata about the current recording."""
        conf = json.loads(self.broadcaster.piloting_conf)
        url = self.url + f"/instances/_definst_/streamrecorders/{conf['livestream']}"
        empty = {
            "currentFile": "",
            "segmentNumber": "",
            "outputPath": "",
            "durationInSeconds": "",
        }
        try:
            resp = requests.get(url, headers={"Accept": "application/json"}, timeout=5)
        except requests.RequestException:
            return empty
        if resp.status_code != http.HTTPStatus.OK:
            return empty
        data = resp.json()
        current_file = data.get("currentFile", "")
        segment_number = ""
        if current_file:
            try:
                ending = current_file.split("_")[-1]
                if re.match(r"\d+\.", ending):
                    num = int(ending.split(".")[0])
                    if num > 0:
                        segment_number = str(num)
            except (IndexError, ValueError):
                pass
        duration = timedelta(
            milliseconds=int(data.get("segmentDuration", 0))
        ).total_seconds()
        return {
            "currentFile": current_file,
            "segmentNumber": segment_number,
            "outputPath": data.get("outputPath", ""),
            "durationInSeconds": int(duration),
        }

    def copy_file_to_pod_dir(self, filename: str) -> bool:
        """Copy recorded file to Pod directory (no-op for Wowza)."""
        return False  # Wowza writes directly to the Pod filesystem

    def can_manage_stream(self) -> bool:
        """Return True if stream can be started/stopped."""
        return False

    def start_stream(self) -> bool:
        """Start the RTMP stream."""
        return False

    def stop_stream(self) -> bool:
        """Stop the RTMP stream."""
        return False

    def get_stream_rtmp_infos(self) -> dict:
        """Return RTMP configuration information."""
        return {}


# ---------------------------------------------------------------------------
# SMP implementation
# ---------------------------------------------------------------------------


class Smp(PilotingInterface):
    """Piloting implementation for SMP (Smart Media Producer) recorders."""

    def __init__(self, broadcaster):
        """Initialise the piloting implementation for the given broadcaster."""
        self.broadcaster = broadcaster
        self.url: str | None = None
        self.use_opencast = False
        if self.check_piloting_conf():
            conf = json.loads(broadcaster.piloting_conf)
            self.url = f"{conf['server_url']}/api/swis/resources"
            self.use_opencast = conf.get("use_opencast", "").lower() == "true"

    def video_creation_method(self) -> str:
        return CREATE_VIDEO_OPENCAST if self.use_opencast else CREATE_VIDEO_FROM_FTP

    def can_split(self) -> bool:
        return False

    def check_piloting_conf(self) -> bool:
        return validate_json_implementation(self.broadcaster)

    def _auth(self):
        """Return (user, password) tuple from piloting_conf."""
        conf = json.loads(self.broadcaster.piloting_conf)
        return (conf["user"], conf["password"])

    def _get(self, uri: str) -> requests.Response | None:
        """Perform a GET request to the SMP API."""
        try:
            return requests.get(
                f"{self.url}?uri={uri}",
                headers={"Accept": "application/json"},
                auth=self._auth(),
                timeout=5,
            )
        except requests.RequestException as exc:
            logger.error("SMP GET %s failed: %s", uri, exc)
            return None

    def _put(self, body) -> requests.Response | None:
        """Perform a PUT request to the SMP API."""
        try:
            return requests.put(
                self.url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                auth=self._auth(),
                data=json.dumps(body),
                timeout=10,
            )
        except requests.RequestException as exc:
            logger.error("SMP PUT failed: %s", exc)
            return None

    @staticmethod
    def _verify(response, key: str, value) -> bool:
        """Verify SMP response contains expected key/value pair."""
        if response is None or response.status_code != http.HTTPStatus.OK:
            return False
        for item in response.json() or []:
            if item.get(key) == value:
                return True
            for v in item.values():
                if isinstance(v, dict) and v.get(key) == value:
                    return True
        return False

    def is_available_to_record(self) -> bool:
        """Check if broadcaster is online and available to record."""
        return self._verify(self._get("/record/state"), "result", "stopped")

    def is_recording(self, with_file_check: bool = False) -> bool:
        """Check if the broadcaster is currently recording."""
        return self._verify(self._get("/record/state"), "result", "recording")

    def start_recording(self, event_id: int) -> bool:
        """Send start-record command to the Wowza server."""
        from src.apps.live.models import Event

        event = Event.objects.filter(id=event_id).first()
        filename = event.slug if event else f"{event_id}_{self.broadcaster.slug}"
        owner = event.owner.username if event else "unknown"
        body = [
            {"uri": "/record/1/root_dir_fs", "value": "internal"},
            {
                "uri": "/record/control",
                "value": {
                    "recording": "record",
                    "location": "internal",
                    "metadata": {
                        "course_id": event_id,
                        "creator": owner,
                        "title": filename,
                    },
                },
            },
        ]
        return self._verify(self._put(body), "recording", "record")

    def split_recording(self) -> bool:
        """Split the current recording segment."""
        logger.error("Smp.split_recording should never be called.")
        return False

    def stop_recording(self) -> bool:
        """Send stop-record command to the device."""
        return self._verify(
            self._put([{"uri": "/record/control", "value": "stop"}]), "result", "stop"
        )

    def get_info_current_record(self) -> dict:
        """Return metadata about the current recording."""
        empty = {
            "currentFile": "",
            "segmentNumber": "",
            "outputPath": "",
            "durationInSeconds": "",
        }
        resp = self._get("/record")
        if resp is None or resp.status_code != http.HTTPStatus.OK or not resp.json():
            return empty
        infos = resp.json()[0].get("result", {})
        if not infos:
            return empty
        return {
            "currentFile": infos.get("filename", ""),
            "segmentNumber": "",
            "outputPath": infos.get("root_dir_fs", ""),
            "durationInSeconds": infos.get("elapsed_time", ""),
        }

    def copy_file_to_pod_dir(self, filename: str) -> bool:
        """Copy recorded file to Pod directory (no-op for Wowza)."""
        if self.use_opencast:
            return True
        try:
            import paramiko
        except ImportError:
            logger.error("paramiko is not installed. Cannot copy file via SFTP.")
            return False

        conf = json.loads(self.broadcaster.piloting_conf)
        from src.apps.live.conf import live_settings

        ftp_host = re.sub(r"https?://", "", conf["server_url"])
        try:
            transport = paramiko.Transport((ftp_host, int(conf["sftp_port"])))
            transport.connect(None, conf["user"], conf["password"])
            sftp = paramiko.SFTPClient.from_transport(transport)
            src_path = os.path.join(conf["record_dir_path"], filename)
            dst_path = os.path.join(
                live_settings.default_event_path, os.path.basename(filename)
            )
            sftp.get(src_path, dst_path)
            sftp.close()
            return True
        except OSError as exc:
            logger.error("SFTP copy failed: %s", exc)
            return False

    def can_manage_stream(self) -> bool:
        """Return True if stream can be started/stopped."""
        return True

    def start_stream(self) -> bool:
        """Start the RTMP stream."""
        return self._set_stream_status(1)

    def stop_stream(self) -> bool:
        """Stop the RTMP stream."""
        return self._set_stream_status(0)

    def _set_stream_status(self, value: int) -> bool:
        """Set SMP RTMP stream status (0=stop, 1=start)."""
        conf = json.loads(self.broadcaster.piloting_conf)
        body = [
            {
                "uri": f"/streamer/rtmp/{conf['rtmp_streamer_id']}/pub_control",
                "value": value,
            }
        ]
        return self._verify(self._put(body), "result", value)

    def get_stream_rtmp_infos(self) -> dict:
        """Return RTMP configuration information."""
        conf = json.loads(self.broadcaster.piloting_conf)
        resp = self._get(f"/streamer/rtmp/{conf['rtmp_streamer_id']}")
        if resp is None or resp.status_code != http.HTTPStatus.OK or not resp.json():
            return {"error": "Failed to fetch RTMP infos"}
        streamer = resp.json()[0]
        result = streamer.get("result", {})
        meta = streamer.get("meta", {})
        if (
            result.get("pub_url")
            and "pub_control" in result
            and "pub_while_record" in result
            and meta.get("uri")
        ):
            return {
                "streamer_id": int(conf["rtmp_streamer_id"]),
                "auto_start_on_record": bool(result["pub_while_record"]),
                "is_streaming": bool(result["pub_control"]),
            }
        return {}
