"""
Django management command that orchestrates Runner Manager tasks.

This command is intended to run periodically (typically via cron) and keeps
the remote-processing pipeline healthy across three task types:
`encoding`, `transcription`, and `studio`.

Execution flow:
1. Resolve the target Django `Site` (current site by default, or `--site`).
2. Detect "stalled" tasks:
   - Looks for tasks still marked `running` in Pod for more than 2 hours.
   - Queries the remote runner (`task/status/<task_id>`).
   - If the remote status is `completed` or `warning`, it triggers result
     retrieval so Pod can finalize local state.
3. Refresh rank metadata for pending tasks.
4. Load pending tasks by type:
   - `encoding` and `transcription` are sorted by user priority
     (non-students first), then by submission date.
   - `studio` tasks are processed by submission date.
   - Each type is capped by `--max-tasks`.
5. Submit tasks to available runner managers (ordered by manager priority):
   - Build payload (`source_url`, `notify_url`, parameters, metadata).
   - Try each runner until one accepts the task.
   - Persist `task_id`, `runner_manager`, and returned status in Pod.
6. Refresh ranks again and clean old completed tasks according to
   `RM_TASKS_DELETED_AFTER_DAYS`.

Important behavior:
- If no runner manager exists for the site, submission is skipped.
- Network/API errors on one runner do not stop processing; the command tries
the next configured runner.
- Cleanup is skipped when `RM_TASKS_DELETED_AFTER_DAYS` is missing, invalid,
  or <= 0.

CLI:
- `python manage.py process_tasks`
- `python manage.py process_tasks --max-tasks 20 --site example.org`

Example cron (every 3 minutes):
`*/3 * * * * /usr/bin/bash -c 'export WORKON_HOME=/home/pod/.virtualenvs; export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3; cd /usr/local/django_projects/podv4; source /usr/local/bin/virtualenvwrapper.sh; workon django_pod4; python manage.py process_tasks >> /usr/local/django_projects/podv4/pod/log/process_tasks.log 2>&1'`
"""

import json
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.utils import timezone

from pod.cut.models import CutVideo
from pod.dressing.models import Dressing
from pod.recorder.models import Recording
from pod.video.models import Video
from pod.video_encode_transcript.models import RunnerManager, Task
from pod.video_encode_transcript.runner_manager_utils import (
    store_before_remote_encoding_recording,
    store_before_remote_encoding_video,
)
from pod.video_encode_transcript.task_queue import (
    get_user_priority,
    refresh_pending_task_ranks,
)
from pod.video_encode_transcript.views import download_and_import_task_result

log = logging.getLogger(__name__)


def handle_stalled_task(task: Task, status: str) -> None:
    """
    Handle a task that is still running in Pod but completed by the runner manager.

    Args:
        task: Task object
        status: Current status from runner manager
    """
    # Problem found: task not completed on Pod side but completed on runner manager
    # Retrieve data from runner manager
    log.info(
        f"Task {task.id} is still running on Pod side, but {status} on runner manager side, retrieving data"
    )
    download_and_import_task_result(task)


class Command(BaseCommand):
    help = "Process encoding tasks: check running tasks and submit pending tasks to runner managers"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--max-tasks",
            type=int,
            default=20,
            help="Maximum number of pending tasks to process in one run (default: 20)",
        )
        parser.add_argument(
            "--site",
            type=str,
            default=None,
            help="Site domain to filter tasks (default: current site)",
        )

    def print_log(self, message: str) -> None:
        """
        Print a plain log message to command stdout.

        Args:
            message: Message to display

        Returns:
            None
        """
        self.stdout.write(message)

    def print_warning(self, message: str) -> None:
        """
        Print a warning-styled message to command stdout.

        Args:
            message: Warning message to display

        Returns:
            None
        """
        self.stdout.write(self.style.WARNING(message))

    def print_error(self, message: str) -> None:
        """
        Print an error-styled message to command stdout.

        Args:
            message: Error message to display

        Returns:
            None
        """
        self.stdout.write(self.style.ERROR(message))

    def print_success(self, message: str) -> None:
        """
        Print a success-styled message to command stdout.

        Args:
            message: Success message to display

        Returns:
            None
        """
        self.stdout.write(self.style.SUCCESS(message))

    def _sort_tasks_by_priority(self, all_pending_tasks, max_tasks: int) -> list:
        """
        Sort encoding tasks by priority (non-students first) and limit to max_tasks.

        Args:
            all_pending_tasks: QuerySet of all pending tasks
            max_tasks: Maximum number of tasks to return

        Returns:
            list: List of tasks sorted by priority and limited to max_tasks
        """
        tasks_with_priority = []
        for task in all_pending_tasks:
            try:
                priority = get_user_priority(task.video) if task.video else 1
                tasks_with_priority.append((priority, task))
            except Video.DoesNotExist:
                log.warning(f"Video {task.video_id} not found for task {task.id}")
                # Still add the task with default priority to avoid skipping it
                tasks_with_priority.append((1, task))

        # Sort by priority (1 first, then 2) and date_added, then limit
        tasks_with_priority.sort(key=lambda x: (x[0], x[1].date_added))
        return [task for _, task in tasks_with_priority[:max_tasks]]

    def _get_site(self, site_domain: str | None) -> Site | None:
        """
        Get the site object based on domain or return current site.

        Args:
            site_domain: Domain name or None for current site

        Returns:
            Site object or None if not found
        """
        if site_domain:
            try:
                return Site.objects.get(domain=site_domain)
            except Site.DoesNotExist:
                self.print_error(f"Site {site_domain} not found")
                return None
        return Site.objects.get_current()

    def _check_task_status(self, task: Task) -> str | None:
        """
        Check the status of a running task from the runner manager.

        Args:
            task: Task object with runner_manager and task_id

        Returns:
            str: Status from runner manager or None if check failed
        """
        if not task.runner_manager or not task.task_id:
            log.warning(f"Task {task.id} has no runner_manager or task_id")
            return None

        try:
            status_url = task.runner_manager.url
            if not status_url.endswith("/"):
                status_url += "/"
            status_url += f"task/status/{task.task_id}"

            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {task.runner_manager.token}",
            }

            response = requests.get(status_url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                log.info(f"Task {task.id} status from runner: {status}")
                return status
            else:
                log.warning(
                    f"Failed to get status for task {task.id}: "
                    f"HTTP {response.status_code}"
                )
                return None
        except requests.RequestException as exc:
            log.warning(f"Cannot reach runner manager for task {task.id}: {str(exc)}")
            return None
        except Exception as exc:
            log.error(f"Error checking status for task {task.id}: {str(exc)}")
            return None

    def _check_running_tasks(self, site: Site) -> None:
        """
        Check running tasks that have been running for more than 2 hours.

        Args:
            site: Site object to filter tasks
        """
        two_hours_ago = timezone.now() - timedelta(hours=2)

        # Get tasks that are running for more than 2 hours (encoding + transcription)
        stalled_tasks = Task.objects.filter(
            type__in=["encoding", "transcription"],
            status="running",
            date_added__lt=two_hours_ago,
        ).select_related("runner_manager")

        if not stalled_tasks:
            self.print_log("No stalled running tasks found")
            return

        self.print_log(
            f"Found {stalled_tasks.count()} task(s) running for more than 2 hours"
        )

        for task in stalled_tasks:
            self.print_log(f"Checking status of task {task.id}...")
            status = self._check_task_status(task)

            # Handle based on status
            if status == "completed" or status == "warning":
                # Problem found: task not completed on Pod side
                # Retrieve data from runner manager
                self.print_warning(
                    f"Task {task.id} is {status}, retrieving data from runner manager"
                )
                handle_stalled_task(task, status)
            elif status == "running":
                # Still running, wait longer
                self.print_success(
                    f"Task {task.id} is still {status}, waiting longer before taking action"
                )
            elif status:
                # Still not completed, no action taken
                self.print_warning(f"Task {task.id} is still {status}, no action taken")
            else:
                self.print_error(f"Could not verify status of task {task.id}")

    def _process_tasks(
        self, pending_tasks: list, site: Site, runner_managers: list
    ) -> int:
        """
        Process each pending encoding task and submit to runner managers.

        Args:
            pending_tasks: List of tasks to process
            site: Site object
            runner_managers: List of available runner managers

        Returns:
            int: Number of successfully submitted tasks
        """
        success_count = 0
        for task in pending_tasks:
            try:
                video = Video.objects.get(id=task.video_id)
                priority = get_user_priority(video)
                priority_label = "LOW (student)" if priority == 2 else "HIGH"
                self.print_log(
                    f"Processing task {task.id} for video {video.id} - Priority: {priority_label}"
                )
                result = self._submit_encoding_task(video, task, site, runner_managers)
                if result:
                    success_count += 1
                    self.print_success(
                        f"Successfully submitted encoding task for video {video.id}"
                    )
                else:
                    self.print_warning(
                        f"Could not submit encoding task for video {video.id} (no runner available)"
                    )
            except Video.DoesNotExist:
                self.print_error(f"Video {task.video_id} not found for task {task.id}")
            except Exception as exc:
                self.print_error(
                    f"Error processing task {task.id} for video {task.video_id}: {str(exc)}"
                )
        return success_count

    def _process_studio_tasks(
        self, pending_tasks: list, site: Site, runner_managers: list
    ) -> int:
        """
        Process each pending studio task (Recording) and submit to runner managers.

        Args:
            pending_tasks: List of studio tasks to process
            site: Site object
            runner_managers: List of available runner managers

        Returns:
            int: Number of successfully submitted tasks
        """
        success_count = 0
        for task in pending_tasks:
            try:
                recording = Recording.objects.get(id=task.recording_id)
                self.print_log(
                    f"Processing studio task {task.id} for recording {recording.id}"
                )
                result = self._submit_studio_task(
                    recording, task, site, runner_managers
                )
                if result:
                    success_count += 1
                    self.print_success(
                        f"Successfully submitted studio task for recording {recording.id}"
                    )
                else:
                    self.print_warning(
                        f"Could not submit studio task for recording {recording.id} (no runner available)"
                    )
            except Recording.DoesNotExist:
                self.print_error(
                    f"Recording {task.recording_id} not found for task {task.id}"
                )
            except Exception as exc:
                self.print_error(
                    f"Error processing studio task {task.id} for recording {task.recording_id}: {str(exc)}"
                )
        return success_count

    def _process_transcription_tasks(
        self, pending_tasks: list, site: Site, runner_managers: list
    ) -> int:
        """
        Process pending transcription tasks and submit them to runner managers.

        Args:
            pending_tasks: List of tasks to process
            site: Current site
            runner_managers: List of available runner managers

        Returns:
            int: Number of successfully submitted tasks
        """
        success_count = 0
        for task in pending_tasks:
            try:
                video = Video.objects.get(id=task.video_id)
                priority = get_user_priority(video)
                priority_label = "LOW (student)" if priority == 2 else "HIGH"
                self.print_log(
                    f"Processing transcription task {task.id} for video {video.id} - Priority: {priority_label}"
                )
                result = self._submit_transcription_task(
                    video, task, site, runner_managers
                )
                if result:
                    success_count += 1
                    self.print_success(
                        f"Successfully submitted transcription task for video {video.id}"
                    )
                else:
                    self.print_warning(
                        f"Could not submit transcription task for video {video.id} (no runner available)"
                    )
            except Video.DoesNotExist:
                self.print_error(f"Video {task.video_id} not found for task {task.id}")
            except Exception as exc:
                self.print_error(
                    f"Error processing transcription task {task.id} for video {task.video_id}: {str(exc)}"
                )
        return success_count

    def _delete_old_completed_tasks(self) -> int:
        """
        Delete completed tasks older than RM_TASKS_DELETED_AFTER_DAYS days.

        Returns:
            int: Number of deleted tasks
        """
        retention_setting = getattr(settings, "RM_TASKS_DELETED_AFTER_DAYS", None)

        if retention_setting is None:
            self.print_log("Skipping cleanup: RM_TASKS_DELETED_AFTER_DAYS is not set")
            return 0

        try:
            retention_days = int(retention_setting)
        except (TypeError, ValueError):
            self.print_error("RM_TASKS_DELETED_AFTER_DAYS must be an integer")
            return 0

        if retention_days <= 0:
            self.print_log("Skipping cleanup: RM_TASKS_DELETED_AFTER_DAYS is <= 0")
            return 0

        cutoff_date = timezone.now() - timedelta(days=retention_days)
        old_tasks = Task.objects.filter(status="completed", date_added__lt=cutoff_date)
        deleted_count = old_tasks.count()

        if deleted_count:
            old_tasks.delete()
            self.print_success(
                f"Deleted {deleted_count} completed task(s) older than {retention_days} day(s)"
            )
            log.info(
                "Deleted %s completed task(s) older than %s day(s)",
                deleted_count,
                retention_days,
            )
        else:
            self.print_log("No completed tasks to delete")

        return deleted_count

    def handle(self, *args, **options) -> None:
        max_tasks = options["max_tasks"]
        site_domain = options["site"]

        # Get site
        site = self._get_site(site_domain)
        if not site:
            return

        self.print_log(f"Processing tasks for site: {site.domain}")
        self.print_log("=" * 60)

        # First, check running tasks that might be stalled
        self.print_log("\n1. Checking running tasks...")
        self._check_running_tasks(site)

        # Then, process pending tasks
        self.print_log("\n2. Processing pending encoding tasks...")
        refresh_pending_task_ranks()

        # Get pending encoding tasks (without limiting to max_tasks yet)
        all_pending_tasks = (
            Task.objects.filter(
                type="encoding",
                status="pending",
            )
            .select_related("video", "video__owner", "video__owner__owner")
            .order_by("date_added")
        )

        # Also get pending studio tasks
        all_pending_studio_tasks = (
            Task.objects.filter(
                type="studio",
                status="pending",
            )
            .select_related("recording")
            .order_by("date_added")
        )

        # Also get pending transcription tasks
        all_pending_transcription_tasks = (
            Task.objects.filter(
                type="transcription",
                status="pending",
            )
            .select_related("video", "video__owner", "video__owner__owner")
            .order_by("date_added")
        )

        if (
            not all_pending_tasks
            and not all_pending_studio_tasks
            and not all_pending_transcription_tasks
        ):
            self.print_success(
                "No pending tasks found (encoding, transcription or studio)"
            )
            self.print_log("\n3. Cleaning completed tasks...")
            self._delete_old_completed_tasks()
            return

        self.print_log(f"Found {all_pending_tasks.count()} pending encoding task(s)")
        self.print_log(
            f"Found {all_pending_studio_tasks.count()} pending studio task(s)"
        )
        self.print_log(
            f"Found {all_pending_transcription_tasks.count()} pending transcription task(s)"
        )

        # Sort tasks by priority (students last) and limit to max_tasks
        pending_tasks = self._sort_tasks_by_priority(all_pending_tasks, max_tasks)
        pending_studio_tasks = list(all_pending_studio_tasks[:max_tasks])
        pending_transcription_tasks = self._sort_tasks_by_priority(
            all_pending_transcription_tasks, max_tasks
        )

        self.print_log(
            f"Processing {len(pending_tasks)} task(s) after priority sorting"
        )

        # Get available runner managers for this site
        runner_managers = list(
            RunnerManager.objects.filter(site=site).order_by("priority")
        )

        if not runner_managers:
            self.print_warning(
                f"No runner manager defined for site {site.domain}. Cannot process tasks."
            )
            return

        # Process each pending task
        success_count_encoding = self._process_tasks(
            pending_tasks, site, runner_managers
        )
        success_count_studio = self._process_studio_tasks(
            pending_studio_tasks, site, runner_managers
        )
        success_count_transcription = self._process_transcription_tasks(
            pending_transcription_tasks, site, runner_managers
        )
        refresh_pending_task_ranks()

        self.print_log("\n3. Cleaning completed tasks...")
        self._delete_old_completed_tasks()

        self.print_success(
            f"Completed: encoding {success_count_encoding}/{len(pending_tasks)}; "
            f"transcription {success_count_transcription}/{len(pending_transcription_tasks)}; "
            f"studio {success_count_studio}/{len(pending_studio_tasks)} successfully submitted"
        )

    def _submit_encoding_task(
        self, video: Video, task: Task, site: Site, runner_managers: list
    ) -> bool:
        """
        Try to submit an encoding task to available runner managers.
        Returns True if successful, False otherwise.
        """
        VERSION = getattr(settings, "VERSION", "4.X")
        TEMPLATE_VISIBLE_SETTINGS = getattr(
            settings,
            "TEMPLATE_VISIBLE_SETTINGS",
            {
                "TITLE_SITE": "Pod",
                "TITLE_ETB": "University name",
            },
        )
        __TITLE_SITE__ = TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE", "Pod")
        __TITLE_ETB__ = TEMPLATE_VISIBLE_SETTINGS.get("TITLE_ETB", "University name")

        base_url = self._build_base_url(site)
        content_url = self._build_content_url(video, base_url)
        parameters = self._prepare_encoding_parameters(video, base_url)

        data = {
            "etab_name": f"{__TITLE_ETB__} / {__TITLE_SITE__}",
            "app_name": "Esup-Pod",
            "app_version": f"{VERSION}",
            "task_type": "encoding",
            "source_url": f"{content_url}",
            "notify_url": f"{base_url}/runner/notify_task_end/",
            "parameters": parameters,
        }

        return self._post_encoding_to_runner(data, task, video, runner_managers)

    def _build_base_url(self, site: Site) -> str:
        SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
        url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
        return f"{url_scheme}://{site.domain}"

    def _build_content_url(self, video: Video, base_url: str) -> str:
        return "%s/media/%s" % (base_url, video.video)

    def _prepare_encoding_parameters(self, video: Video, base_url: str) -> dict:
        from pod.video_encode_transcript.encoding_utils import get_list_rendition

        list_rendition = get_list_rendition()
        str_resolution = {
            str(k): {"resolution": v["resolution"], "encode_mp4": v["encode_mp4"]}
            for k, v in list_rendition.items()
        }
        parameters = {"rendition": json.dumps(str_resolution)}

        cut_info = self._get_cut_info(video)
        if cut_info:
            parameters["cut"] = json.dumps(cut_info)

        dressing_info = self._get_dressing_info(video, base_url)
        if dressing_info:
            parameters["dressing"] = json.dumps(dressing_info)

        return parameters

    def _get_cut_info(self, video: Video) -> dict | None:
        try:
            cut_video = CutVideo.objects.get(video=video)
            return {
                "start": str(cut_video.start),
                "end": str(cut_video.end),
                "initial_duration": str(cut_video.duration),
            }
        except CutVideo.DoesNotExist:
            return None

    def _get_dressing_info(self, video: Video, base_url: str) -> dict | None:
        try:
            if not Dressing.objects.filter(videos=video).exists():
                return None
            dressing = Dressing.objects.get(videos=video)
            if not dressing:
                return None
            str_dressing_info: dict = {}
            if dressing.watermark:
                watermark_content_url = "%s/media/%s" % (
                    base_url,
                    str(dressing.watermark.file.name),
                )
                str_dressing_info["watermark"] = watermark_content_url
                str_dressing_info["watermark_position"] = dressing.position
                str_dressing_info["watermark_opacity"] = str(dressing.opacity)
            if dressing.opening_credits:
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
                str_dressing_info["ending_credits"] = dressing.ending_credits.slug
                ending_content_url = "%s/media/%s" % (
                    base_url,
                    str(dressing.ending_credits.video.name),
                )
                str_dressing_info["ending_credits_video"] = ending_content_url
                str_dressing_info["ending_credits_video_duration"] = str(
                    dressing.ending_credits.duration
                )
            return str_dressing_info or None
        except Exception as exc:
            log.warning(
                "Error retrieving dressing for video id: %s, %s", video.id, str(exc)
            )
            return None

    def _post_encoding_to_runner(
        self, data: dict, task: Task, video: Video, runner_managers: list
    ) -> bool:
        for runner_manager in runner_managers:
            try:
                execute_url = runner_manager.url
                if not execute_url.endswith("/"):
                    execute_url += "/"
                execute_url += "task/execute"

                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {runner_manager.token}",
                }

                response = requests.post(
                    execute_url, data=json.dumps(data), headers=headers, timeout=30
                )

                if response.status_code == 200:
                    task_id = response.json().get("task_id")
                    status = response.json().get("status")

                    task.status = status
                    task.runner_manager = runner_manager
                    task.task_id = task_id
                    task.save()
                    store_before_remote_encoding_video(video.id, execute_url, data)

                    log.info(
                        f"Successfully submitted encoding task for video {video.id} to runner manager {runner_manager.name}"
                    )
                    return True
                log.warning(
                    f"Runner manager {runner_manager.name} returned status code {response.status_code}"
                )
            except requests.RequestException as exc:
                log.warning(
                    f"Cannot reach runner manager {runner_manager.name}: {str(exc)}"
                )

        return False

    def _submit_transcription_task(
        self, video: Video, task: Task, site: Site, runner_managers: list
    ) -> bool:
        """
        Try to submit a transcription task to available runner managers.
        Returns True if successful, False otherwise.
        """
        from pod.video_encode_transcript.transcript import (
            resolve_transcription_language,
        )

        # Get settings
        SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
        VERSION = getattr(settings, "VERSION", "4.X")
        TEMPLATE_VISIBLE_SETTINGS = getattr(
            settings,
            "TEMPLATE_VISIBLE_SETTINGS",
            {
                "TITLE_SITE": "Pod",
                "TITLE_ETB": "University name",
            },
        )
        __TITLE_SITE__ = TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE", "Pod")
        __TITLE_ETB__ = TEMPLATE_VISIBLE_SETTINGS.get("TITLE_ETB", "University name")

        # Build content URL: prefer mp3 if available, else video file
        url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
        base_url = url_scheme + "://" + site.domain
        mp3 = video.get_video_mp3() if hasattr(video, "get_video_mp3") else None
        if mp3 and getattr(mp3, "source_file", None) and getattr(mp3, "url", None):
            content_url = f"{base_url}{mp3.url}"
        else:
            content_url = f"{base_url}/media/{video.video}"

        # Prepare transcription parameters (aligned with runner_manager._prepare_transcription_parameters)
        transcription_type = getattr(settings, "TRANSCRIPTION_TYPE", None)
        normalize = bool(getattr(settings, "TRANSCRIPTION_NORMALIZE", False))
        params = {
            "language": resolve_transcription_language(video),
            "duration": float(getattr(video, "duration", 0) or 0),
            "normalize": normalize,
        }
        if transcription_type:
            params["model_type"] = transcription_type

        data = {
            "etab_name": f"{__TITLE_ETB__} / {__TITLE_SITE__}",
            "app_name": "Esup-Pod",
            "app_version": f"{VERSION}",
            "task_type": "transcription",
            "source_url": f"{content_url}",
            "notify_url": f"{base_url}/runner/notify_task_end/",
            "parameters": params,
        }

        # Try each runner manager
        for runner_manager in runner_managers:
            try:
                execute_url = runner_manager.url
                if not execute_url.endswith("/"):
                    execute_url += "/"
                execute_url += "task/execute"

                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {runner_manager.token}",
                }

                response = requests.post(
                    execute_url, data=json.dumps(data), headers=headers, timeout=30
                )

                if response.status_code == 200:
                    task_id = response.json().get("task_id")
                    status = response.json().get("status")

                    # Update task
                    task.status = status
                    task.runner_manager = runner_manager
                    task.task_id = task_id
                    task.save()

                    log.info(
                        f"Successfully submitted transcription task for video {video.id} to runner manager {runner_manager.name}"
                    )
                    return True
                else:
                    log.warning(
                        f"Runner manager {runner_manager.name} returned status code {response.status_code}"
                    )
            except requests.RequestException as exc:
                log.warning(
                    f"Cannot reach runner manager {runner_manager.name}: {str(exc)}"
                )

        return False

    def _submit_studio_task(
        self, recording: Recording, task: Task, site: Site, runner_managers: list
    ) -> bool:
        """
        Try to submit a studio task (recording XML link) to available runner managers.
        Returns True if successful, False otherwise.
        """
        # Get settings
        SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
        VERSION = getattr(settings, "VERSION", "4.X")
        TEMPLATE_VISIBLE_SETTINGS = getattr(
            settings,
            "TEMPLATE_VISIBLE_SETTINGS",
            {
                "TITLE_SITE": "Pod",
                "TITLE_ETB": "University name",
            },
        )
        __TITLE_SITE__ = TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE", "Pod")
        __TITLE_ETB__ = TEMPLATE_VISIBLE_SETTINGS.get("TITLE_ETB", "University name")

        # Build source XML URL from MEDIA_ROOT to MEDIA_URL
        url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
        base_url = url_scheme + "://" + site.domain
        media_url = getattr(settings, "MEDIA_URL", "/media/").rstrip("/")
        try:
            import os

            rel_path = os.path.relpath(
                str(recording.source_file), str(getattr(settings, "MEDIA_ROOT", ""))
            )
        except Exception:
            rel_path = str(recording.source_file)
        rel_path = rel_path.lstrip("/")
        source_url = f"{base_url}{media_url}/{rel_path}"

        # Parameters: same rendition payload as for video, no cut
        from pod.video_encode_transcript.encoding_utils import get_list_rendition

        list_rendition = get_list_rendition()
        str_resolution = {
            str(k): {"resolution": v["resolution"], "encode_mp4": v["encode_mp4"]}
            for k, v in list_rendition.items()
        }
        json_resolution = json.dumps(str_resolution)
        parameters = {"rendition": json_resolution}

        data = {
            "etab_name": f"{__TITLE_ETB__} / {__TITLE_SITE__}",
            "app_name": "Esup-Pod",
            "app_version": f"{VERSION}",
            "task_type": "studio",
            "source_url": f"{source_url}",
            "notify_url": f"{base_url}/runner/notify_task_end/",
            "parameters": parameters,
        }

        # Try each runner manager
        for runner_manager in runner_managers:
            try:
                execute_url = runner_manager.url
                if not execute_url.endswith("/"):
                    execute_url += "/"
                execute_url += "task/execute"

                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {runner_manager.token}",
                }

                response = requests.post(
                    execute_url, data=json.dumps(data), headers=headers, timeout=30
                )

                if response.status_code == 200:
                    task_id = response.json().get("task_id")
                    status = response.json().get("status")

                    # Update task with studio type
                    task.status = status
                    task.runner_manager = runner_manager
                    task.task_id = task_id
                    task.save()
                    store_before_remote_encoding_recording(
                        recording.id, execute_url, data
                    )

                    log.info(
                        f"Successfully submitted studio task for recording {recording.id} to runner manager {runner_manager.name}"
                    )
                    return True
                else:
                    log.warning(
                        f"Runner manager {runner_manager.name} returned status code {response.status_code}"
                    )
            except requests.RequestException as exc:
                log.warning(
                    f"Cannot reach runner manager {runner_manager.name}: {str(exc)}"
                )

        return False
