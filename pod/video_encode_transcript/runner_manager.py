"""Runner Manager orchestration helpers for encoding and transcription tasks in Esup-Pod.

This module builds task payloads, dispatches them to available runner managers,
and keeps local task rows synchronized with runner-side task status.
"""

import json
import logging
import os
from typing import Any, Literal, Optional, TypeAlias, TypedDict, Union, cast

import requests
from django.conf import settings
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from pod.cut.models import CutVideo
from pod.recorder.models import Recording
from pod.video.models import Video
from pod.video_encode_transcript.models import RunnerManager, Task
from pod.video_encode_transcript.runner_manager_utils import (
    store_before_remote_encoding_recording,
    store_before_remote_encoding_video,
)

from .utils import change_encoding_step

if __name__ == "__main__":
    from encoding_utils import get_list_rendition
else:
    from .encoding_utils import get_list_rendition

log = logging.getLogger(__name__)

DEBUG = getattr(settings, "DEBUG", True)

# Settings for template customization
TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/esup-pod.svg",
        "LOGO_PLAYER": "img/pod_favicon.svg",
        "LINK_PLAYER": "",
        "LINK_PLAYER_NAME": _("Home"),
        "FOOTER_TEXT": ("",),
        "FAVICON": "img/pod_favicon.svg",
        "CSS_OVERRIDE": "",
        "PRE_HEADER_TEMPLATE": "",
        "POST_FOOTER_TEMPLATE": "",
        "TRACKING_TEMPLATE": "",
    },
)
__TITLE_SITE__ = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)
__TITLE_ETB__ = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_ETB"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_ETB"))
    else "University name"
)

VERSION = getattr(settings, "VERSION", "4.X")

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)


SourceType = Literal["video", "recording"]
TaskType = Literal["encoding", "studio", "transcription"]
ParametersDict: TypeAlias = dict[str, Any]
HeadersDict: TypeAlias = dict[str, str]


class RunnerManagerTaskPayload(TypedDict):
    """Task payload expected by the Runner Manager API."""

    etab_name: str
    app_name: str
    app_version: str
    task_type: TaskType
    source_url: str
    notify_url: str
    parameters: ParametersDict


class RunnerManagerResponse(TypedDict, total=False):
    """Relevant fields returned by the Runner Manager API."""

    task_id: str
    status: str


def _build_rendition_parameters() -> ParametersDict:
    """Return rendition parameters serialized for the runner payload."""
    list_rendition = get_list_rendition()
    str_resolution: dict[str, dict[str, Any]] = {
        str(k): {"resolution": v["resolution"], "encode_mp4": v["encode_mp4"]}
        for k, v in list_rendition.items()
    }
    return {"rendition": json.dumps(str_resolution)}


def _attach_cut_info(parameters: ParametersDict, video: Video) -> None:
    """Attach cut information to parameters if it exists for the given video."""
    try:
        cut_video = CutVideo.objects.get(video=video)
        str_cut_info = {
            "start": str(cut_video.start),
            "end": str(cut_video.end),
            "initial_duration": str(cut_video.duration),
        }
        parameters["cut"] = json.dumps(str_cut_info)
    except CutVideo.DoesNotExist:
        pass


def _attach_dressing_info(parameters: ParametersDict, video: Video) -> None:
    """Attach dressing information to parameters if available for the given video."""
    try:
        from pod.dressing.models import Dressing

        site = Site.objects.get_current()
        url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
        base_url = url_scheme + "://" + site.domain

        str_dressing_info = {}
        if Dressing.objects.filter(videos=video).exists():
            log.info("Dressing found for video id: %s", video.id)
            dressing = Dressing.objects.get(videos=video)
            if dressing:
                if dressing.watermark:
                    log.info("Dressing watermark found")
                    watermark_content_url = "%s/media/%s" % (
                        base_url,
                        str(dressing.watermark.file.name),
                    )
                    str_dressing_info["watermark"] = watermark_content_url
                    str_dressing_info["watermark_position"] = dressing.position
                    str_dressing_info["watermark_opacity"] = str(dressing.opacity)
                if dressing.opening_credits:
                    log.info("Dressing opening credits found")
                    str_dressing_info["opening_credits"] = dressing.opening_credits.slug
                    opening_content_url = "%s/media/%s" % (
                        base_url,
                        str(dressing.opening_credits.video.name),
                    )
                    str_dressing_info["opening_credits_video"] = opening_content_url
                    str_dressing_info["opening_credits_video_duration"] = str(
                        dressing.opening_credits.duration
                    )
                if dressing.ending_credits:
                    log.info("Dressing ending credits found")
                    str_dressing_info["ending_credits"] = dressing.ending_credits.slug
                    ending_content_url = "%s/media/%s" % (
                        base_url,
                        str(dressing.ending_credits.video.name),
                    )
                    str_dressing_info["ending_credits_video"] = ending_content_url
                    str_dressing_info["ending_credits_video_duration"] = str(
                        dressing.ending_credits.duration
                    )
                    # str_dressing_info["ending_credits_video_hasaudio"] = str(
                    #     dressing.ending_credits.video.has_audio()
                    # )
        if str_dressing_info:
            parameters["dressing"] = json.dumps(str_dressing_info)
    except Exception as exc:
        log.error(f"Error obtaining dressing for video {video.id}: {str(exc)}")


def _prepare_encoding_parameters(
    video: Optional[Video] = None,
) -> ParametersDict:
    """Prepare encoding parameters for video or recording.

    Args:
        video: Video object (for video encoding).
               For studio recordings, pass None as cut info doesn't apply.

    Returns:
        Dictionary with rendition and optionally cut information
    """
    parameters = _build_rendition_parameters()

    if video:
        _attach_cut_info(parameters, video)
        _attach_dressing_info(parameters, video)

    return parameters


def _prepare_task_data(
    source_url: str,
    base_url: str,
    parameters: ParametersDict,
    task_type: TaskType,
) -> RunnerManagerTaskPayload:
    """Prepare task payload for runner manager.

    Args:
        source_url: URL to the source file (video or XML)
        base_url: Base URL of the site
        parameters: Encoding parameters

    Returns:
        Dictionary with task data
    """
    return {
        "etab_name": f"{__TITLE_ETB__} / {__TITLE_SITE__}",
        "app_name": "Esup-Pod",
        "app_version": VERSION,
        "task_type": task_type,
        "source_url": source_url,
        "notify_url": f"{base_url}/runner/notify_task_end/",
        "parameters": parameters,
    }


# ---- Runner manager helpers (module-level to keep complexity low) ----
def _rotate_same_priority_runner_managers(
    runner_managers: list[RunnerManager],
) -> list[RunnerManager]:
    """Rotate a same-priority runner manager list using last assigned task."""
    if len(runner_managers) <= 1:
        return runner_managers

    runner_manager_ids = [rm.id for rm in runner_managers]
    last_runner_manager_id = (
        Task.objects.filter(runner_manager_id__in=runner_manager_ids)
        .order_by("-date_added", "-id")
        .values_list("runner_manager_id", flat=True)
        .first()
    )
    if not last_runner_manager_id or last_runner_manager_id not in runner_manager_ids:
        return runner_managers

    last_index = runner_manager_ids.index(last_runner_manager_id)
    return runner_managers[last_index + 1 :] + runner_managers[: last_index + 1]


def _get_runner_managers(site: Site) -> list[RunnerManager]:
    """Return active site runner managers ordered by priority with round-robin per priority."""
    ordered_runner_managers = list(
        RunnerManager.objects.filter(site=site, is_active=True).order_by(
            "priority", "id"
        )
    )
    if len(ordered_runner_managers) <= 1:
        return ordered_runner_managers

    runner_managers: list[RunnerManager] = []
    current_priority: Optional[int] = None
    current_group: list[RunnerManager] = []
    # Apply round-robin only inside groups that share the same priority level.
    for runner_manager in ordered_runner_managers:
        if current_priority is None or runner_manager.priority == current_priority:
            current_group.append(runner_manager)
            current_priority = runner_manager.priority
            continue

        runner_managers.extend(_rotate_same_priority_runner_managers(current_group))
        current_group = [runner_manager]
        current_priority = runner_manager.priority

    if current_group:
        runner_managers.extend(_rotate_same_priority_runner_managers(current_group))

    return runner_managers


def _ids_for(
    source_type: SourceType, source_id: Union[int, str]
) -> tuple[Optional[int], Optional[int]]:
    """Return (video_id, recording_id) tuple based on source type."""
    return (int(source_id), None) if source_type == "video" else (None, int(source_id))


def _execute_url(rm: RunnerManager) -> str:
    """Build the execute endpoint URL for the given runner manager."""
    base = rm.url if rm.url.endswith("/") else rm.url + "/"
    return base + "task/execute"


def _headers(rm: RunnerManager) -> HeadersDict:
    """Build authentication and content headers for the runner manager API."""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {rm.token}",
    }


def _try_send_to_rm(
    rm: RunnerManager, payload: RunnerManagerTaskPayload
) -> Optional[requests.Response]:
    """Try to POST the payload to a runner manager; log and return None on failure."""
    try:
        return requests.post(
            _execute_url(rm), data=json.dumps(payload), headers=_headers(rm), timeout=30
        )
    except requests.RequestException as exc:
        log.warning(
            f"Cannot reach runner manager {rm.name}: {str(exc)}. Trying next one."
        )
        return None


def _prestore_encoding_if_needed(
    *,
    task_type: TaskType,
    source_type: SourceType,
    video_id: Optional[int],
    recording_id: Optional[int],
    rm: RunnerManager,
    data: RunnerManagerTaskPayload,
) -> None:
    """Run pre-store steps for encoding/studio tasks.

    Does nothing for transcription tasks.
    """
    if task_type not in ("encoding", "studio"):
        return
    execute_url = _execute_url(rm)
    if source_type == "video":
        if video_id is not None:
            store_before_remote_encoding_video(video_id, execute_url, data)
        else:
            log.warning(
                "Unexpected None video_id for source_type 'video' while preparing store_before_remote_encoding_video."
            )
    elif source_type == "recording":
        if recording_id is not None:
            store_before_remote_encoding_recording(recording_id, execute_url, data)
        else:
            log.warning(
                "Unexpected None recording_id for source_type 'recording' while preparing store_before_remote_encoding_recording."
            )


def _submit_to_runner_manager(
    rm: RunnerManager,
    data: RunnerManagerTaskPayload,
    task_type: TaskType,
    source_type: SourceType,
    video_id: Optional[int],
    recording_id: Optional[int],
) -> bool:
    """Submit payload to one runner manager and handle response and pre-store."""
    response = _try_send_to_rm(rm, data)
    if response is None:
        return False
    if response.status_code != 200:
        log.warning(
            f"Runner manager {rm.name} returned status code {response.status_code}. Trying next one."
        )
        return False
    log.info(
        f"Runner manager {rm.name} is available to process {task_type} for {source_type} {video_id or recording_id}."
    )
    # Runner may reply with no body; keep an empty payload in that case.
    payload = cast(RunnerManagerResponse, response.json() if response.content else {})
    _update_task_from_response(video_id, recording_id, task_type, rm, payload)
    _prestore_encoding_if_needed(
        task_type=task_type,
        source_type=source_type,
        video_id=video_id,
        recording_id=recording_id,
        rm=rm,
        data=data,
    )
    return True


def _update_task_pending(
    source_type: SourceType, source_id: Union[int, str], task_type: TaskType
) -> tuple[Optional[int], Optional[int]]:
    """Create or set a pending task for the given source and return (video_id, recording_id)."""
    video_id, recording_id = _ids_for(source_type, source_id)
    log.info(
        "Update task to pending for video_id: %s, recording_id: %s",
        video_id,
        recording_id,
    )
    _edit_task(
        video_id=video_id,
        recording_id=recording_id,
        type=task_type,
        status="pending",
        runner_manager_id=None,
        task_id=None,
    )
    return video_id, recording_id


def _update_task_from_response(
    video_id: Optional[int],
    recording_id: Optional[int],
    task_type: TaskType,
    rm: RunnerManager,
    response_json: RunnerManagerResponse,
) -> None:
    """Update the task row using the response payload returned by the runner manager."""
    task_id = response_json.get("task_id")
    status = str(response_json.get("status", "pending"))
    log.info(
        "Update task for video_id=%s, recording_id=%s, task_type=%s with response_json=%s",
        video_id,
        recording_id,
        task_type,
        response_json,
    )
    _edit_task(
        video_id=video_id,
        recording_id=recording_id,
        type=task_type,
        status=status,
        runner_manager_id=rm.id,
        task_id=task_id,
    )


def _send_task_to_runner_manager(
    *,
    task_type: TaskType,
    source_id: Union[int, str],
    source_type: SourceType,
    source_url: str,
    base_url: str,
    parameters: ParametersDict,
) -> bool:
    """Submit a task to the Runner Manager and update the DB task row.

    - task_type: one of "encoding", "studio", "transcription"
    - source_type: "video" or "recording" (used to resolve ids and pre-store behavior)
    """

    try:
        # Keep a local pending row even when no runner is currently available.
        # This allows process_tasks to retry submission later.
        video_id, recording_id = _update_task_pending(source_type, source_id, task_type)

        site = Site.objects.get_current()
        runner_managers_list = _get_runner_managers(site)
        if not runner_managers_list:
            log.warning(
                f"No active runner manager defined for site {site.domain}. Cannot process {task_type} for {source_type} {source_id}."
            )
            return False

        # Build payload and try immediate submission
        data = _prepare_task_data(source_url, base_url, parameters, task_type)

        # Try each runner manager by priority and stop on the first healthy one.
        for rm in runner_managers_list:
            if _submit_to_runner_manager(
                rm,
                data=data,
                task_type=task_type,
                source_type=source_type,
                video_id=video_id,
                recording_id=recording_id,
            ):
                return True

        log.warning(
            f"No runner manager available to process {task_type} for {source_type} {source_id}. "
            f"Task will remain pending and will be retried by the process_tasks command."
        )
        return False

    except Exception as exc:
        log.error(
            f"Error to process {task_type} for {source_type} {source_id}: {str(exc)}"
        )
        return False


def encode_video(video_id: int) -> None:
    """Start video encoding with runner manager."""
    log.info("Start encoding, with runner manager, for id: %s" % video_id)
    try:
        site = Site.objects.get_current()
        # Get video info
        video = get_object_or_404(Video, id=video_id)
        # Build content URL
        url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
        base_url = url_scheme + "://" + site.domain
        content_url = "%s/media/%s" % (base_url, video.video)

        # Prepare encoding parameters
        parameters = _prepare_encoding_parameters(video=video)

        # Send encoding task to runner manager
        _send_task_to_runner_manager(
            task_type="encoding",
            source_id=video_id,
            source_type="video",
            source_url=content_url,
            base_url=base_url,
            parameters=parameters,
        )

    except Exception as exc:
        log.error(
            'Error to encode video "%(id)s": %(exc)s'
            % {"id": video_id, "exc": str(exc)}
        )


def encode_studio_recording(recording_id: int) -> None:
    """Start encoding studio recording with runner manager.

    This function handles encoding of studio recordings by passing the XML
    source file URL to the runner manager.
    """
    log.info(
        "Start encoding, with runner manager, for studio recording id %s" % recording_id
    )
    try:
        site = Site.objects.get_current()
        # Get studio recording
        recording = Recording.objects.get(id=recording_id)
        # Source file corresponds to Pod XML file
        source_file = recording.source_file

        # Build source file URL.
        # `source_file` is sometimes an absolute MEDIA_ROOT path and sometimes already relative.
        url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
        base_url = url_scheme + "://" + site.domain
        media_url = getattr(settings, "MEDIA_URL", "/media/").rstrip("/")
        try:
            rel_path = os.path.relpath(
                str(source_file), str(getattr(settings, "MEDIA_ROOT", ""))
            )
        except Exception:
            rel_path = str(source_file)
        rel_path = rel_path.lstrip("/")
        source_url = f"{base_url}{media_url}/{rel_path}"

        # Prepare encoding parameters (no specific cut info for studio recordings)
        parameters = _prepare_encoding_parameters(video=None)

        # Send studio task to runner manager
        _send_task_to_runner_manager(
            task_type="studio",
            source_id=recording_id,
            source_type="recording",
            source_url=source_url,
            base_url=base_url,
            parameters=parameters,
        )

    except Recording.DoesNotExist:
        log.error(f"Recording {recording_id} not found.")
    except Exception as exc:
        log.error(f"Error to encode recording {recording_id}: {str(exc)}")


def transcript_video(video_id: int) -> None:
    """Start video transcription with runner manager."""
    log.info("Start transcription, with runner manager, for id: %s" % video_id)
    try:
        site = Site.objects.get_current()
        # Get video info
        video = get_object_or_404(Video, id=video_id)
        # Get associated mp3 file if exists
        mp3file = video.get_video_mp3().source_file if video.get_video_mp3() else None
        url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
        base_url = url_scheme + "://" + site.domain
        if mp3file is not None:
            content_url = "%s%s" % (base_url, mp3file.url)
        else:
            # Build video content URL
            content_url = "%s/media/%s" % (base_url, video.video)

        # Prepare transcript parameters
        parameters = _prepare_transcription_parameters(video=video)

        # Mark video as encoding in progress
        video_to_encode = Video.objects.get(id=video_id)
        video_to_encode.encoding_in_progress = True
        video_to_encode.save()

        # Update encoding step to transcripting audio
        change_encoding_step(video_id, 5, "transcripting audio")

        # Send transcription task to runner manager
        _send_task_to_runner_manager(
            task_type="transcription",
            source_id=video_id,
            source_type="video",
            source_url=content_url,
            base_url=base_url,
            parameters=parameters,
        )

    except Exception as exc:
        log.error(
            'Error to transcribe video "%(id)s": %(exc)s'
            % {"id": video_id, "exc": str(exc)}
        )


def _prepare_transcription_parameters(video: Video) -> ParametersDict:
    """Prepare parameters for a transcription task.

    Args:
        video: `Video` instance to transcribe.

    Returns:
        Parameter dictionary for the Runner Manager.
    """
    try:
        from .transcript import resolve_transcription_language

        # Requested language (video `transcript` field)
        lang = resolve_transcription_language(video)

        # Options from settings (optional on runner side)
        transcription_type = getattr(settings, "TRANSCRIPTION_TYPE", None)
        normalize = bool(getattr(settings, "TRANSCRIPTION_NORMALIZE", False))

        params: ParametersDict = {
            "language": lang,
            # Duration may help runner to tune/optimize
            "duration": float(getattr(video, "duration", 0) or 0),
            # Text normalization (punctuation/casing) on runner side if supported
            "normalize": normalize,
        }
        # If needed in future, we can add model size or other options here
        if transcription_type:
            params["model_type"] = transcription_type
            # Possibility to add model size if needed in future
            # params["model"] = "medium"

        return params
    except Exception:
        # Keep legacy key name for backward compatibility with older runners.
        return {"lang": getattr(video, "transcript", "") or ""}


def _edit_task(
    video_id: Optional[int],
    type: str,
    status: str,
    runner_manager_id: Optional[int] = None,
    task_id: Optional[str] = None,
    recording_id: Optional[int] = None,
) -> None:
    """Edit or create a task for a video or studio recording."""
    try:
        from .task_queue import refresh_pending_task_ranks

        log.info(
            f"Edit or create a task: {video_id} {type} {runner_manager_id} {status} {task_id}"
        )
        # Check if a task already exists for this video and type with pending status
        # Build base queryset depending on source type
        if type == "studio":
            tasks_list = list(
                Task.objects.filter(
                    recording_id=recording_id,
                    type=type,
                    status="pending",
                )
            )
        else:
            tasks_list = list(
                Task.objects.filter(
                    video_id=video_id,
                    type=type,
                    status="pending",
                )
            )
        if not tasks_list:
            # Create new task
            task = Task(
                video_id=video_id if type != "studio" else None,
                recording_id=recording_id if type == "studio" else None,
                type=type,
                runner_manager_id=runner_manager_id,
                status=status,
                task_id=task_id,
            )
            task.save()
        else:
            # Edit existing task
            task = tasks_list[0]
            task.status = status
            if runner_manager_id is not None:
                task.runner_manager_id = runner_manager_id
            if task_id is not None:
                task.task_id = task_id
            # Keep association fields as-is
            task.save()

        refresh_pending_task_ranks()

    except Exception as exc:
        log.error(
            f"Unable to edit a task (video_id={video_id}, recording_id={recording_id}): {str(exc)}"
        )
