"""Views and helpers, useful only for Runner Manager callbacks and artifact imports in Esup-Pod.

This module handles the full post-processing flow for remote tasks:
- validate and authorize webhook notifications,
- download task result files from the Runner Manager,
- import artifacts back into Pod (encoding, studio, transcription).
"""

import json
import logging
import os
import random
import secrets
import shutil
import tempfile
import time
from hashlib import sha256
from typing import TypeAlias, TypedDict, cast

import requests
import webvtt
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from pod.recorder.models import Recording
from pod.recorder.plugins.type_studio import save_basic_video
from pod.video.models import Video
from pod.video_encode_transcript.models import RunnerManager, Task
from pod.video_encode_transcript.runner_manager_utils import (
    store_after_remote_encoding_video,
    store_remote_encoding_log_recording,
)
from pod.video_encode_transcript.task_queue import refresh_pending_task_ranks
from pod.video_encode_transcript.transcript import save_vtt_and_notify
from pod.video_encode_transcript.utils import send_email_item

log = logging.getLogger(__name__)

DEBUG = getattr(settings, "DEBUG", True)
MANIFEST_MEMBER_DOWNLOAD_MAX_RETRIES = 5
MANIFEST_MEMBER_DOWNLOAD_BACKOFF_BASE_SECONDS = 0.5
MANIFEST_MEMBER_DOWNLOAD_BACKOFF_MAX_SECONDS = 8.0

media_root_setting = getattr(settings, "MEDIA_ROOT", None)
if not media_root_setting:
    raise RuntimeError("MEDIA_ROOT is not configured in settings")
MEDIA_ROOT = str(media_root_setting)

VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")

HeadersDict: TypeAlias = dict[str, str]


def _get_media_root() -> str:
    """Return MEDIA_ROOT from settings at runtime."""
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if not media_root:
        raise RuntimeError("MEDIA_ROOT is not configured in settings")
    return str(media_root)


def _get_videos_dir() -> str:
    """Return VIDEOS_DIR from settings at runtime."""
    return str(getattr(settings, "VIDEOS_DIR", "videos"))


def _format_video_directory(video_id: int | str) -> str:
    """Return normalized video directory name using at least 4 digits."""
    try:
        return f"{int(video_id):04d}"
    except (TypeError, ValueError):
        return str(video_id)


class NotifyTaskPayload(TypedDict, total=False):
    """Payload sent by Runner Manager to the notify endpoint."""

    task_id: str
    status: str
    script_output: str
    error_message: str


class ResultManifest(TypedDict, total=False):
    """Manifest returned by the Runner Manager result endpoint."""

    files: list[object]


class ManifestMemberIntegrityError(RuntimeError):
    """Raised when a downloaded manifest member fails integrity validation."""


def _build_result_url(manager_url: str, task_id: str) -> str:
    """Return runner manager result URL ending with trailing slash."""
    if not manager_url.endswith("/"):
        manager_url += "/"
    return manager_url + f"task/result/{task_id}"


def _build_result_file_url(manager_url: str, task_id: str, file_path: str) -> str:
    """Return runner manager file URL for a given task result file."""
    if not manager_url.endswith("/"):
        manager_url += "/"
    return manager_url + f"task/result/{task_id}/file/{file_path}"


def _build_headers(token: str) -> HeadersDict:
    """Construct headers used when querying runner manager."""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def _build_file_headers(token: str) -> HeadersDict:
    """Construct headers used when downloading files from runner manager."""
    return {
        "Accept": "*/*",
        "Authorization": f"Bearer {token}",
    }


def _extract_bearer_token(request: WSGIRequest) -> str | None:
    """Return token from Authorization header when using Bearer scheme."""
    authorization = request.headers.get("Authorization", "")
    auth_type, _, token = authorization.partition(" ")
    token = token.strip()
    if auth_type.lower() != "bearer" or not token:
        return None
    return token


def _fetch_task_result(
    url: str, headers: HeadersDict, task_id: int | str
) -> requests.Response | None:
    """Return HTTP response for a task result or None on failure."""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        log.info(f"Fetched result for task {task_id}: {url}")
    except requests.RequestException as exc:
        log.error(f"Error reaching runner manager for task {task_id}: {exc}")
        return None
    if response.status_code != 200:
        log.error(
            f"Failed to download result for task {task_id}: {response.status_code} {response.text}"
        )
        return None
    return response


def _finalize_task_import(
    task: Task, extracted_dir: str, extracted_vtt_path: str
) -> None:
    """Persist result path and import artifacts based on task type."""
    if hasattr(task, "result_path"):
        task.result_path = extracted_dir
    task.save()

    try:
        if task.type == "studio" or getattr(task, "recording_id", None):
            # Studio tasks generate a new Video from the base media before importing artifacts.
            video_id = _create_video_from_studio_task(task)
            recording_id = task.recording_id
            if recording_id is None:
                raise RuntimeError(
                    "Studio task missing recording_id after video creation"
                )
            store_remote_encoding_log_recording(recording_id, video_id)
            store_after_remote_encoding_video(video_id)
        elif task.type == "transcription":
            _import_transcription_result(task, extracted_vtt_path)
        else:
            store_after_remote_encoding_video(task.video.id)
        task.status = "completed"
        task.save()
    except Exception as exc:  # noqa: BLE001
        log.error(f"Error while importing result for task {task.id}: {exc}")


def _parse_notify_task_end_request(
    request: WSGIRequest,
) -> tuple[NotifyTaskPayload | None, str | None, JsonResponse | None]:
    """Validate request shape and return parsed JSON payload with bearer token."""
    if request.method != "POST":
        return (
            None,
            None,
            JsonResponse({"error": "Only POST requests are allowed."}, status=405),
        )

    content_type = request.headers.get("Content-Type") or ""
    if "application/json" not in content_type:
        return (
            None,
            None,
            JsonResponse(
                {"error": "Only application/json content type is allowed."}, status=415
            ),
        )

    bearer_token = _extract_bearer_token(request)
    if not bearer_token:
        return (
            None,
            None,
            JsonResponse({"error": "Missing or invalid Bearer token."}, status=401),
        )

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return None, None, JsonResponse({"error": "Invalid request."}, status=400)

    if not isinstance(payload, dict):
        return None, None, JsonResponse({"error": "Invalid request."}, status=400)

    data = cast(NotifyTaskPayload, payload)
    return data, bearer_token, None


def _get_notify_task(
    data: NotifyTaskPayload,
) -> tuple[Task | None, JsonResponse | None]:
    """Fetch task referenced in notification payload."""
    task_id = data.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        return None, JsonResponse({"error": "No task id in the request."}, status=400)

    task = Task.objects.filter(task_id=task_id).select_related("runner_manager").first()
    if not task:
        return None, JsonResponse({"error": "Task not found."}, status=404)

    return task, None


def _authorize_notify_task(task: Task, bearer_token: str) -> JsonResponse | None:
    """Check bearer token against the task runner manager token."""
    runner_manager = task.runner_manager
    if not runner_manager or not runner_manager.token:
        log.error("Task %s has no runner manager token configured", task.task_id)
        return JsonResponse(
            {"error": "Runner manager token is not configured."},
            status=500,
        )

    if not secrets.compare_digest(bearer_token, runner_manager.token):
        return JsonResponse({"error": "Invalid Bearer token."}, status=403)

    return None


def _apply_notify_payload_to_task(task: Task, data: NotifyTaskPayload) -> None:
    """Persist task status and append optional script output details."""
    task.status = str(data["status"])

    script_output = task.script_output or ""
    error_message = data.get("error_message")
    if error_message is not None:
        script_output += f"{error_message}\n---\n"
    script_output_payload = data.get("script_output")
    if script_output_payload is not None:
        script_output += str(script_output_payload)

    task.script_output = script_output
    task.save()
    refresh_pending_task_ranks()


@csrf_exempt
def notify_task_end(request: WSGIRequest) -> JsonResponse:
    """Receive webhook from the Runner Manager service."""
    data, bearer_token, error_response = _parse_notify_task_end_request(request)
    if error_response:
        return error_response

    if data is None or bearer_token is None:
        return JsonResponse({"error": "Invalid request."}, status=400)

    task, error_response = _get_notify_task(data)
    if error_response:
        return error_response

    if task is None:
        return JsonResponse({"error": "Task not found."}, status=404)

    error_response = _authorize_notify_task(task, bearer_token)
    if error_response:
        return error_response

    if "status" not in data:
        return JsonResponse(
            {"status": "Task has not yet been successfully achieved."},
            status=500,
        )

    _apply_notify_payload_to_task(task, data)

    if task.status == "failed":
        send_email_item(f"Task {task.id} failed", "Task", task.task_id)

    if task.status == "completed":
        download_and_import_task_result(task)

    return JsonResponse({"status": "OK"}, status=200)


def _get_runner_manager_for_task(task: Task) -> RunnerManager | None:
    """Return task runner manager if available, otherwise log and return None."""
    try:
        return RunnerManager.objects.get(id=task.runner_manager_id)
    except RunnerManager.DoesNotExist:
        log.error(f"Runner manager not found for task {task.id}")
        return None
    except Exception as exc:  # noqa: BLE001
        log.error(f"Error downloading result for task {task.id}: {exc}")
        return None


def _get_task_result_manifest(
    task: Task, runner_manager: RunnerManager
) -> ResultManifest | None:
    """Fetch and validate task result manifest from runner manager."""
    if not task.task_id:
        log.error(f"Missing task_id for task {task.id}")
        return None

    result_url = _build_result_url(runner_manager.url, task.task_id)
    headers = _build_headers(runner_manager.token)
    response = _fetch_task_result(result_url, headers, task.id)
    if not response:
        return None

    try:
        manifest_payload = response.json()
    except ValueError:
        manifest_payload = {}

    if not isinstance(manifest_payload, dict):
        log.error(f"Invalid manifest JSON for task {task.id}")
        return None

    manifest = cast(ResultManifest, manifest_payload)
    if not manifest.get("files"):
        log.error(f"Invalid manifest JSON for task {task.id}")
        return None

    return manifest


def download_and_import_task_result(task: Task) -> None:
    """Download the result of a completed task from the runner manager, extract it,
    and import the encoded video back into Pod.

    Args:
        task (Task): Task object
    """
    runner_manager = _get_runner_manager_for_task(task)
    if not runner_manager:
        return

    manifest = _get_task_result_manifest(task, runner_manager)
    if manifest is None:
        return

    extracted_dir, extracted_vtt_path = _save_manifest_files(
        manifest, task, runner_manager.url, runner_manager.token
    )

    if not extracted_dir:
        log.error(f"Failed to import result for task {task.id}")
        return

    log.info(f"Successfully downloaded and extracted result for task {task.id}")
    _finalize_task_import(task, extracted_dir, extracted_vtt_path)


def _import_transcription_result(task: Task, extracted_vtt_path: str) -> None:
    """Import a transcription result produced by the Runner Manager.

    Expected: at least one .vtt file in the extracted directory.
    It will be attached to the related video. Language defaults to the
    video's `transcript` field (fallback to main_lang when empty).

    Args:
        task: Task of type "transcription" linked to a `Video`.
        extracted_vtt_path: Path to the extracted VTT file.
    """
    if not getattr(task, "video", None):
        raise RuntimeError("Transcription task is not linked to a video")

    log.info(f"Importing VTT file {extracted_vtt_path} for video {task.video.id}")

    # Get the video
    video_id = task.video.id
    video = Video.objects.get(id=video_id)
    # Default message
    msg = f"Transcription imported successfully: {extracted_vtt_path}"
    # Read the VTT file
    wvtt = webvtt.read(extracted_vtt_path)
    # Save VTT for Pod and notify user
    save_vtt_and_notify(video, msg, wvtt)
    log.info(f"Attached VTT transcript to video {video.id}")


def _get_destination_directory(task: Task, dest_base: str | None = None) -> str:
    """Get and create the destination directory for extraction.

    Args:
        task (Task): Task instance used to name the destination directory.
        dest_base (str | None): parent directory where to extract.
    Returns:
        str: path of the destination directory.
    """
    if dest_base is None:
        # Choose base directory based on task type (encoding, studio or transcription)
        if task.type == "transcription" and getattr(task, "video", None):
            video_dir = _format_video_directory(task.video.id)
            dest_dir = os.path.join(
                MEDIA_ROOT,
                VIDEOS_DIR,
                str(task.video.owner.owner.hashkey),
                video_dir,
            )
        elif task.type == "studio":
            dest_dir = os.path.join(MEDIA_ROOT, "tasks", str(task.id))
        else:
            video_dir = _format_video_directory(task.video.id)
            dest_dir = os.path.join(
                MEDIA_ROOT,
                VIDEOS_DIR,
                str(task.video.owner.owner.hashkey),
                video_dir,
            )
        log.info(f"Save result into {dest_dir}")
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
    else:
        dest_dir = os.path.join(dest_base, str(task.id))
        os.makedirs(dest_dir, exist_ok=True)
    return dest_dir


def _is_safe_path(dest_dir: str, member: str) -> bool:
    """Check whether a manifest entry path is safe to write.

    Args:
        dest_dir (str): The destination directory.
        member (str): The manifest file path to validate.
    Returns:
        bool: True if the path is safe, False otherwise.
    """
    member_path = os.path.normpath(member)
    # Skip absolute paths and parent-traversal entries
    if member_path.startswith("..") or os.path.isabs(member_path):
        return False
    dest_path = os.path.normpath(os.path.join(dest_dir, member_path))
    normalized_dest = os.path.normpath(dest_dir)
    # Ensure extraction is within destination directory
    return dest_path.startswith(normalized_dest + os.sep) or dest_path == normalized_dest


def _should_extract_transcription_member(member: str) -> bool:
    """Return True when member must be extracted for transcription tasks."""
    if member.endswith("/"):
        return False
    base_l = os.path.basename(member).lower()
    return base_l.endswith(".vtt") or base_l.endswith(".json")


def _should_download_manifest_member(task: Task, dest_dir: str, file_path: str) -> bool:
    """Return True when the given manifest entry should be downloaded."""
    if not file_path:
        return False

    if task.type == "transcription" and not _should_extract_transcription_member(
        file_path
    ):
        return False

    if not _is_safe_path(dest_dir, file_path):
        log.warning(f"Ignored suspicious manifest file path: {file_path}")
        return False

    return True


def _download_manifest_member(
    url: str,
    headers: HeadersDict,
    file_path: str,
    task: Task,
) -> requests.Response | None:
    """Download a single manifest member file."""
    try:
        response = requests.get(url, headers=headers, timeout=60, stream=True)
    except requests.RequestException as exc:
        log.error(f"Error downloading file {file_path} for task {task.id}: {exc}")
        return None

    if response.status_code != 200:
        log.error(
            "Failed to download file %s for task %s: %s %s",
            file_path,
            task.id,
            response.status_code,
            response.text,
        )
        return None

    return response


def _store_manifest_member(
    response: requests.Response,
    dest_dir: str,
    file_path: str,
    expected_sha256: str | None = None,
) -> str:
    """Write a downloaded manifest member to disk and return destination path."""
    dest_path = os.path.normpath(os.path.join(dest_dir, file_path))
    parent = os.path.dirname(dest_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    if file_path.endswith("/"):
        os.makedirs(dest_path, exist_ok=True)
        return dest_path

    temp_path = _create_manifest_temp_path(parent or dest_dir)
    try:
        actual_sha256 = _stream_manifest_member_to_tempfile(response, temp_path)
        _validate_manifest_member_checksum(file_path, expected_sha256, actual_sha256)
        os.replace(temp_path, dest_path)
    except Exception:
        _remove_file_if_exists(temp_path)
        raise

    return dest_path


def _create_manifest_temp_path(temp_dir: str) -> str:
    """Create and return an empty temporary file path for atomic writes."""
    temp_file_descriptor, temp_path = tempfile.mkstemp(
        prefix=".manifest_",
        suffix=".part",
        dir=temp_dir,
    )
    os.close(temp_file_descriptor)
    return temp_path


def _stream_manifest_member_to_tempfile(
    response: requests.Response, temp_path: str
) -> str:
    """Stream response content to temp_path and return computed SHA-256."""
    checksum = sha256()
    with open(temp_path, "wb") as target:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            target.write(chunk)
            checksum.update(chunk)
    return checksum.hexdigest()


def _validate_manifest_member_checksum(
    file_path: str,
    expected_sha256: str | None,
    actual_sha256: str,
) -> None:
    """Raise on checksum mismatch when manifest provides an expected hash."""
    if expected_sha256 is None:
        return
    if actual_sha256 == expected_sha256:
        return
    raise ManifestMemberIntegrityError(
        f"Checksum mismatch for {file_path}: expected {expected_sha256}"
    )


def _remove_file_if_exists(path: str) -> None:
    """Delete file if present, ignoring absence and cleanup race conditions."""
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError:
        pass


def _parse_manifest_member_entry(
    task: Task, manifest_entry: object
) -> tuple[str | None, str | None]:
    """Extract (file_path, optional_sha256) from one manifest entry."""
    if isinstance(manifest_entry, str):
        return manifest_entry, None

    if not isinstance(manifest_entry, dict):
        log.warning(
            "Ignored manifest entry with unsupported format for task %s: %r",
            task.id,
            manifest_entry,
        )
        return None, None

    file_path = manifest_entry.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        alt_file_path = manifest_entry.get("path")
        if isinstance(alt_file_path, str) and alt_file_path:
            file_path = alt_file_path
        else:
            log.warning(
                "Ignored manifest entry without file path for task %s: %r",
                task.id,
                manifest_entry,
            )
            return None, None

    checksum_value = manifest_entry.get("sha256")
    if checksum_value is None:
        return file_path, None

    if not isinstance(checksum_value, str):
        log.warning(
            "Ignored non-string sha256 for file %s in task %s",
            file_path,
            task.id,
        )
        return file_path, None

    normalized_checksum = checksum_value.strip().lower()
    if len(normalized_checksum) != 64 or any(
        char not in "0123456789abcdef" for char in normalized_checksum
    ):
        log.warning(
            "Ignored invalid sha256 for file %s in task %s",
            file_path,
            task.id,
        )
        return file_path, None

    return file_path, normalized_checksum


def _compute_manifest_retry_delay(attempt: int) -> float:
    """Return delay in seconds using exponential backoff with full jitter."""
    exponential_delay = min(
        MANIFEST_MEMBER_DOWNLOAD_BACKOFF_MAX_SECONDS,
        MANIFEST_MEMBER_DOWNLOAD_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)),
    )
    return random.uniform(0.0, exponential_delay)


def _download_and_store_manifest_member(
    url: str,
    headers: HeadersDict,
    file_path: str,
    task: Task,
    dest_dir: str,
    expected_sha256: str | None = None,
    max_attempts: int = MANIFEST_MEMBER_DOWNLOAD_MAX_RETRIES,
) -> str | None:
    """Download and store one manifest file with retry and integrity checks."""
    for attempt in range(1, max_attempts + 1):
        response = _download_manifest_member(url, headers, file_path, task)
        if response is None:
            if attempt == max_attempts:
                return None
            retry_delay = _compute_manifest_retry_delay(attempt)
            log.warning(
                "Retrying file %s for task %s after failed request (%s/%s), next try in %.2fs",
                file_path,
                task.id,
                attempt,
                max_attempts,
                retry_delay,
            )
            time.sleep(retry_delay)
            continue

        try:
            return _store_manifest_member(
                response,
                dest_dir,
                file_path,
                expected_sha256=expected_sha256,
            )
        except (requests.RequestException, ManifestMemberIntegrityError) as exc:
            if attempt == max_attempts:
                log.error(
                    "Failed to fully download file %s for task %s after %s attempts: %s",
                    file_path,
                    task.id,
                    max_attempts,
                    exc,
                )
                return None
            retry_delay = _compute_manifest_retry_delay(attempt)
            log.warning(
                "Retrying file %s for task %s after streamed transfer/integrity error (%s/%s), next try in %.2fs: %s",
                file_path,
                task.id,
                attempt,
                max_attempts,
                retry_delay,
                exc,
            )
            time.sleep(retry_delay)
        except OSError as exc:
            log.error(f"Failed to write file {file_path} for task {task.id}: {exc}")
            return None
        finally:
            response.close()
    return None


def _save_manifest_files(
    manifest: ResultManifest,
    task: Task,
    manager_url: str,
    token: str,
    dest_base: str | None = None,
) -> tuple[str | None, str]:
    """Download files listed in a manifest JSON and store them in dest_dir.

    Args:
        manifest: Manifest JSON with at least a "files" list.
        task: Task instance used to name the destination directory.
        manager_url: Runner manager base URL.
        token: Runner manager token for Authorization header.
        dest_base: Optional parent directory where to store.

    Returns:
        (dest_dir, vtt_path) where vtt_path may be empty.
    """
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        log.error(f"Manifest missing files for task {task.id}")
        return None, ""

    if not task.task_id:
        log.error(f"Missing task_id for task {task.id}")
        return None, ""

    dest_dir = _get_destination_directory(task, dest_base)
    dest_vtt_path = ""
    headers = _build_file_headers(token)

    for manifest_entry in files:
        file_path, expected_sha256 = _parse_manifest_member_entry(task, manifest_entry)
        if file_path is None:
            continue

        if not _should_download_manifest_member(task, dest_dir, file_path):
            continue

        url = _build_result_file_url(manager_url, task.task_id, file_path)
        dest_path = _download_and_store_manifest_member(
            url,
            headers,
            file_path,
            task,
            dest_dir,
            expected_sha256=expected_sha256,
        )
        if dest_path is None:
            return None, ""

        if task.type == "transcription" and dest_path.lower().endswith(".vtt"):
            dest_vtt_path = dest_path

    log.info(f"Downloaded manifest files for task {task.id} into {dest_dir}")
    return dest_dir, dest_vtt_path


def _create_video_from_studio_task(task: Task, extracted_dir: str | None = None) -> int:
    """Create a Pod video from a studio task and relocate artifacts.

    Workflow:
    - Validate that the task references a recording (`task.recording_id`).
    - Expect `studio_base.mp4` under MEDIA_ROOT/tasks/<task.id> by default.
    - Create a new Video via `save_basic_video(recording, src_file)`.
    - Move the task extraction directory to MEDIA_ROOT/VIDEOS_DIR/<hashkey>/<%04d video_id>.
    - Return the created video's id.

    Args:
        task: The `Task` instance (must contain `recording_id`).
        extracted_dir: Optional source directory containing extracted studio files.

    Returns:
        int: The created video id.

    Raises:
        RuntimeError: If recording is missing or expected files/directories are not present.
    """
    # Ensure the task is linked to a recording
    if not getattr(task, "recording_id", None):
        raise RuntimeError("Studio task missing recording_id")

    # Compute source file path from extracted_dir or default MEDIA_ROOT/tasks/<task.id>.
    src_dir = extracted_dir or os.path.join(_get_media_root(), "tasks", str(task.id))
    src_file = os.path.join(src_dir, "studio_base.mp4")
    if not os.path.exists(src_file) or not os.path.isfile(src_file):
        raise RuntimeError(f"Source studio file not found: {src_file}")

    # Load recording and create a new Pod video from the base file
    try:
        recording = Recording.objects.get(id=task.recording_id)
        # Create a new Pod video
        video = save_basic_video(recording, src_file)
    except Recording.DoesNotExist:
        raise RuntimeError(f"Recording not found: {task.recording_id}")

    # Move the rest of the task artifacts into the new video directory
    _move_task_directory_to_video(task, video.id, src_dir=src_dir, recording=recording)

    return video.id


def _get_user_hashkey_from_recording(recording: Recording) -> str:
    """Return the user's hashkey from a recording or raise a clear error."""
    try:
        return str(recording.user.owner.hashkey)
    except Exception as exc:
        raise RuntimeError("Unable to resolve recording owner's hashkey") from exc


def _merge_or_move_directory(src_dir: str, dest_dir: str) -> None:
    """Move src_dir to dest_dir; merge contents if destination already exists."""
    # Ensure parent of dest_dir exists
    os.makedirs(os.path.dirname(dest_dir), exist_ok=True)

    # If destination exists, merge contents; else move the whole directory
    if os.path.exists(dest_dir):
        if not os.path.isdir(dest_dir):
            raise RuntimeError(
                f"Destination path exists and is not a directory: {dest_dir}"
            )
        for entry in os.listdir(src_dir):
            src_path = os.path.join(src_dir, entry)
            target_path = os.path.join(dest_dir, entry)
            # If target exists, remove it before move to avoid errors
            if os.path.exists(target_path):
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)
            shutil.move(src_path, dest_dir)
        # Cleanup empty src_dir (best effort)
        try:
            os.rmdir(src_dir)
        except OSError:
            pass
    else:
        shutil.move(src_dir, dest_dir)


def _move_task_directory_to_video(
    task: Task,
    video_id: int,
    src_dir: str | None = None,
    recording: Recording | None = None,
) -> None:
    """Move the task extraction directory into the final video directory.

    Source: MEDIA_ROOT/tasks/<task.id> by default.
    Destination: MEDIA_ROOT/VIDEOS_DIR/<hashkey>/<%04d video_id>

    Args:
        task: The `Task` instance (must contain `recording_id`).
        video_id: The destination video id used to build the target path.
        src_dir: Optional explicit source directory for extracted studio files.
        recording: Optional recording object to avoid loading it twice.

    Raises:
        RuntimeError: When required data or paths are missing.
    """
    if not getattr(task, "id", None):
        raise RuntimeError("Task missing id")

    if not getattr(task, "recording_id", None):
        raise RuntimeError("Task missing recording_id")

    source_dir = src_dir or os.path.join(_get_media_root(), "tasks", str(task.id))
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        raise RuntimeError(f"Source directory not found: {source_dir}")

    if recording is None:
        try:
            recording = Recording.objects.get(id=task.recording_id)
        except Recording.DoesNotExist:
            raise RuntimeError(f"Recording not found: {task.recording_id}")

    user_hashkey = _get_user_hashkey_from_recording(recording)
    video_dir = _format_video_directory(video_id)
    dest_dir = os.path.join(
        _get_media_root(), _get_videos_dir(), user_hashkey, video_dir
    )

    _merge_or_move_directory(source_dir, dest_dir)

    log.info(f"Moved task directory from {source_dir} to {dest_dir}")
