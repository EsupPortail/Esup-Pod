---
layout: default
version: 4.x
lang: en
---

# Remote encoding and transcription via Esup-Runner

> 💡 This documentation only applies to ESUP-Pod versions 4.2.0 and later.

## Purpose

When `USE_RUNNER_MANAGER = True`, ESUP-Pod delegates encoding and transcription processing to one or more Esup-Runner services called Runner Managers.

## Prerequisites

- Install/configure a Runner Manager service: [Esup-Runner](https://github.com/EsupPortail/esup-runner).
- This feature requires **Pod 4.2 or later**.

This document explains:

- the end-to-end functional flow;
- `settings_local.py` configuration;
- the configuration required in the administration interface (Runner managers);
- day-to-day operations in task administration;
- the importance of running the `process_tasks` command regularly via CRON.

## Flow Overview

1. A user (or an internal process) triggers an encoding, transcription, or studio encoding task.
2. Pod creates/sets a local `Task` with `pending` status.
3. Pod attempts to send the task to a Runner Manager (`/task/execute`) using Bearer authentication.
4. If no runner is reachable, the task remains `pending` (it will be retried by `process_tasks`).
5. The runner executes the task, then calls the Pod webhook `POST /runner/notify_task_end/`.
6. Pod updates the task status, then, if `completed`, downloads results (`/task/result/<task_id>`) and imports artifacts.
7. Pod finalizes the task as `completed` and updates business objects (encoded files, subtitles, studio video, etc.).

## `settings_local.py` Configuration

Recommended minimal configuration, in production:

```py
USE_RUNNER_MANAGER = True
RM_TASKS_DELETED_AFTER_DAYS = 60
SECURE_SSL_REDIRECT = True
ENCODE_VIDEO = "start_encode"
FILE_UPLOAD_PERMISSIONS = 0o644
```

### `USE_RUNNER_MANAGER = True`

- Enables offloading mode.
- `start_encode` and `start_transcript` then go through `pod.video_encode_transcript.runner_manager`.
- Also enables the `/runner/notify_task_end/` webhook route in `pod/urls.py`.

### `RM_TASKS_DELETED_AFTER_DAYS = 60`

- Used by the `process_tasks` command.
- Deletes `completed` tasks older than 60 days.
- If missing, invalid, or `<= 0`, cleanup is skipped.

### `SECURE_SSL_REDIRECT = True`

- Used in production to force HTTP-to-HTTPS redirection.
- This setting should already be present; make sure its value is `True`.
- If it is missing, the site remains accessible over HTTP.

### `ENCODE_VIDEO = "start_encode"`

- Function called to start encoding videos.
- This is the default value, so this parameter may be missing from your `settings_local.py`.

### `FILE_UPLOAD_PERMISSIONS = 0o644`

- Defines the permissions Django applies to uploaded files once they are saved to disk.
- The octal value `0o644` allows the owner to read and modify the file, while the group and other users can only read it.
- This setting notably allows the web server to read and serve files created by Pod. It must be consistent with the Nginx configuration, particularly the user specified by the `user` directive in `/etc/pod/nginx.conf` (or `/etc/nginx/nginx.conf`, depending on the installation). See [Web Frontend NGINX / UWSGI and Static Files](../production-mode_en#web-frontend-nginx--uwsgi-and-static-files).

## Configuration via Administration

### 1. Runner Managers Administration

In administration, create at least one Runner Manager:

- `name`: readable name (e.g. `um-rm-gpu01`);
- `priority`: lower value means higher runner priority;
- `url`: Runner Manager base URL;
- `token`: Bearer token shared with this runner;
- `site`: related Django site.

Best practices:

- configure at least 2 runners for fault tolerance;
- use priorities to control routing;
- when priorities are equal, Pod applies round-robin rotation between runners in that group.

### 2. Test Connectivity

On a Runner Manager record, after entering values and saving, use the **Test connection** button:

- Pod calls the `manager/health` endpoint;
- checks network access, URL, and token;
- displays an explicit response (`200/204`, `401/403`, `404`, etc.).

## Operations via Task Administration

The `Task` admin lets you manage the queue:

- view `type` (`encoding`, `transcription`, `studio`);
- track the `status` (`pending`, `running`, `completed`, `failed`, `timeout`);
- view information associated with tasks;
- read the `script_output` field for diagnostics.

Useful action:

- **Restart selected tasks**: sets selected tasks back to `pending`, clears technical fields (`task_id`, runner, script output, rank), then immediately retries sending them to runners.

In parallel, the video interface also shows queue rank (`rank`) and the total number of `pending` tasks.

## Role of `process_tasks` in Operations

The command:

```sh
python manage.py process_tasks
```

is the operational engine to run periodically. It:

1. checks `running` tasks stuck for more than 2 hours and attempts reconciliation with the runner;
2. submits `pending` tasks (encoding, transcription, studio) to available runners;
3. applies priority scheduling (notably non-students before students);
4. updates queue ranks;
5. purges completed tasks according to `RM_TASKS_DELETED_AFTER_DAYS`.

Without running this command repeatedly:

- tasks may remain stuck in `pending`;
- retry/failover to another runner will not happen;
- automatic cleanup is not performed.

## Recommended CRON Scheduling

Example every 3 minutes:

```cron
# Job for Esup-Runner tasks
*/3 * * * * /usr/bin/bash -c 'export WORKON_HOME=/home/pod/.virtualenvs; export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3; cd /usr/local/django_projects/podv4; source /usr/local/bin/virtualenvwrapper.sh; workon django_pod4; python manage.py process_tasks >> /usr/local/django_projects/podv4/pod/log/process_tasks.log 2>&1'
```

Tips:

- monitor the log file regularly;
- adjust frequency according to your workload.

## Go-Live Checklist

1. Enable `USE_RUNNER_MANAGER = True`.
2. Set `RM_TASKS_DELETED_AFTER_DAYS` (e.g. `60`).
3. Create Runner Managers in administration (URL/token/priority/site).
4. Validate each manager using **Test connection**.
5. Deploy the `process_tasks` CRON job.
6. Verify status transitions in `Task` admin: `pending -> running -> completed`.
