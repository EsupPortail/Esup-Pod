<!-- markdownlint-disable MD013 -->
# Import Video: Technical Details

>
> **Navigation:** [Back to Overview](README.md) | [Back to Index](../README.md)

---

## 1. Models

### ExternalRecording

Stores the declaration of an external video source and tracks its import lifecycle (`src/apps/import_video/models/ExternalRecording.py`).

| Field            | Type                  | Description                                                      |
| :--------------- | :-------------------- | :--------------------------------------------------------------- |
| `name`           | CharField             | Display name for the recording.                                  |
| `owner`          | FK → User             | Staff user who declared the recording.                           |
| `site`           | FK → Site             | Site the recording belongs to (multi-tenancy).                   |
| `source_type`    | CharField (choices)   | Source platform (see SourceType below).                          |
| `source_url`     | URLField              | URL of the external video.                                       |
| `import_status`  | CharField (choices)   | Current import pipeline status (see ImportStatus below).         |
| `video`          | OneToOne → Video      | Linked Pod Video after successful import. Null until then.       |
| `error_message`  | TextField             | Error detail if import failed. Empty otherwise.                  |
| `start_at`       | DateTimeField         | Timestamp when the recording was declared.                       |
| `imported_at`    | DateTimeField         | Timestamp when the import completed successfully.                |

**SourceType choices:**

```python
class SourceType(models.TextChoices):
    YOUTUBE    = "youtube"        # YouTube via yt-dlp
    PEERTUBE   = "peertube"       # PeerTube REST API
    BBB        = "bigbluebutton"  # BigBlueButton (standard only)
    VIDEO_FILE = "video"          # Direct MP4/video URL
    MEDIACAD   = "mediacad"       # Mediacad JSON API
```

**ImportStatus choices:**

```python
class ImportStatus(models.TextChoices):
    PENDING    = "pending"     # Not yet started
    PROCESSING = "processing"  # Celery task running
    DONE       = "done"        # Import successful
    ERROR      = "error"       # Import failed
```

---

## 2. Services

Each source type has a dedicated service module in `src/apps/import_video/services/`.

### `downloader.py`

Generic HTTP downloader used by all services.

- `check_video_size(size_bytes)` — raises `ValueError` if size exceeds 4 GB.
- `download_file(url, dest_path)` — streams the file to disk with timeout and error handling.

### `youtube.py`

- `get_youtube_metadata(source_url)` — fetches title, publish date, stream object, and file size via `yt-dlp`.
- `download_youtube_video(source_url, dest_dir)` — checks size and downloads the highest resolution stream.

> **⚠️ Risk**: YouTube API changes may break this service if `yt-dlp` is not kept up to date.

### `peertube.py`

- `get_peertube_metadata(source_url)` — calls `/api/v1/videos/<uuid>` to fetch title, description, and download URL.
- `download_peertube_video(source_url, dest_path)` — delegates to `downloader.download_file`.

Supports both `/videos/watch/<uuid>` and `/w/<uuid>` URL formats.

### `mediacad.py`

- `get_mediacad_metadata(source_url)` — calls the Mediacad JSON API to fetch title and download URL.
- `download_mediacad_video(source_url, dest_path)` — delegates to `downloader.download_file`.

### `bbb.py`

- `get_bbb_standard_metadata(source_url)` — parses the BBB playback HTML page to extract the video source URL.
- `download_bbb_video(source_url, dest_path)` — delegates to `downloader.download_file`.
- `get_bbb_esr_metadata(source_url)` — raises `NotImplementedError` until the Meeting module is migrated to V5.

---

## 3. Celery Task

Located in `src/apps/import_video/tasks.py`.

### `task_import_external_recording(recording_id, user_id)`

Asynchronous Celery task triggered by `POST /api/external-recordings/{id}/import/`.

**Flow:**

```text
1. Load ExternalRecording + User from DB
2. Set import_status = PROCESSING
3. _dispatch_import(recording)
   ├── YOUTUBE   → youtube.download_youtube_video()
   ├── PEERTUBE  → peertube.download_peertube_video()
   ├── BBB       → bbb.download_bbb_video()
   ├── VIDEO     → downloader.download_file()
   └── MEDIACAD  → mediacad.download_mediacad_video()
4. _create_video_from_recording()
   ├── Video.objects.create(title, owner, status=DRAFT)
   ├── video.video_file.save(file)
   ├── video.sites.add(current_site)
   ├── recording.video = video
   ├── recording.import_status = DONE
   └── trigger_runner_encoding_task.delay(video.pk, source_url)
```

**Error handling:**

| Exception             | Outcome                                      |
| :-------------------- | :------------------------------------------- |
| `NotImplementedError` | status → ERROR, message logged as WARNING    |
| `ValueError`          | status → ERROR, message stored               |
| `Exception`           | status → ERROR, full traceback logged        |

---

## 4. Access Control & Permissions

### `CanImportVideo` (`src/apps/import_video/permissions.py`)

| Method            | Rule                                                                 |
| :---------------- | :------------------------------------------------------------------- |
| Safe (`GET`)      | Any authenticated user.                                              |
| Write (`POST`...) | Authenticated. If `restrict_to_staff=True`: staff or superuser only. |

### ViewSet-level checks

- `perform_create`: enforces `restrict_to_staff` before saving.
- `perform_update` / `perform_destroy`: owner or superuser only.
- `import_to_pod`: blocks if already `PROCESSING` or `DONE`.
- `reset_import`: blocks if currently `PROCESSING`.

---

## 5. Serializer

Located in `src/apps/import_video/serializers/ExternalRecordingSerializer.py`.

**Read-only fields:** `id`, `owner`, `import_status`, `import_status_label`, `source_type_label`, `video`, `error_message`, `start_at`, `imported_at`.

**Validations:**

| Rule                        | Description                                                        |
| :-------------------------- | :----------------------------------------------------------------- |
| `validate_source_url`       | Source URL must not be empty.                                      |
| `validate` (YouTube)        | URL must contain `youtube.com` or `youtu.be`.                      |
| `validate` (PeerTube)       | URL must contain `/videos/watch/` or `/w/`.                        |
| `validate` (BBB)            | URL must contain `playback` or `recording`.                        |

---

## 6. Configuration Settings

Managed via `ImportVideoConfig` (`src/apps/import_video/conf.py`). Defaults in `src/config/defaults/import_video.py`.

| Setting               | Default | Description                                          |
| :-------------------- | :------ | :--------------------------------------------------- |
| `USE_IMPORT_VIDEO`    | `False` | Enable/disable the import video feature entirely.    |
| `RESTRICT_TO_STAFF`   | `True`  | Restrict import creation to staff users only.        |

---

## 7. Testing

Run tests for the import_video application:

```bash
pytest src/apps/import_video/tests/
```

Key test files:

- `test_import_video.py`: Tests for ExternalRecording CRUD, permissions, import triggering, and reset.

---

> **Pod V5 Team** | [Documentation Index](../README.md)

## Further Reading

- ⬅️ **[Back to Overview](README.md)**
- ⬅️ **[Back to Index](../README.md)**
