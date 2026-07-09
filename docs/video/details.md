<!-- markdownlint-disable MD013 -->
# Video: Technical Details

> **Navigation:** [Back to Overview](README.md) | [Back to Index](../README.md)

---

## 1. Models

### Video

The central model of the application (`src/apps/video/models/Video.py`).

**Key fields:**

| Field               | Type              | Description                                                       |
| :------------------ | :---------------- | :---------------------------------------------------------------- |
| `title`             | CharField         | Video title (max 250 chars).                                      |
| `slug`              | SlugField         | Auto-generated unique identifier used in URLs (`{title}-{uuid}`). |
| `description`       | TextField         | Full description of the content.                                  |
| `video_file`        | FileField         | Stored under `videos/<username>/<slug>.<ext>`.                    |
| `thumbnail`         | ImageField        | Custom cover image. Falls back to default if absent.              |
| `overview`          | ImageField        | Auto-generated preview image (non-editable).                      |
| `duration`          | IntegerField      | Duration in seconds (set by `ffprobe` post-upload).               |
| `owner`             | FK → User         | Primary owner of the video.                                       |
| `co_owners`         | M2M → User        | Users with edit rights (cannot delete).                           |
| `status`            | CharField         | Current video state (see Status choices below).                   |
| `is_auth_required`  | BooleanField      | Requires login to view, even on restricted videos.                |
| `password`          | CharField         | Optional password hash (PBKDF2-SHA256).                           |
| `allow_downloading` | BooleanField      | Exposes the source file URL in the API response.                  |
| `date_of_event`     | DateField         | Date of the recorded event.                                       |
| `license`           | CharField         | Content license (CC-BY, COPYRIGHT, etc.).                         |
| `cursus`            | CharField         | Academic level (L1–M2, Doctorate, Other).                         |
| `language`          | CharField         | Main spoken language (e.g. `fr`, `en`).                           |
| `date_to_delete`    | DateField         | Auto-computed expiration date based on owner's affiliation.       |
| `type`              | FK → Type         | Essential categorization of the video.                            |
| `disciplines`       | M2M → Discipline  | Associated academic disciplines.                                  |
| `tags`              | TaggableManager   | Custom tags (using tagulous).                                     |
| `sites`             | M2M → Site        | Links the video to specific portals for multi-tenancy.            |
| `restricted_groups` | M2M → AccessGroup | Limits access to specific user groups (when RESTRICTED).          |
| `view_count`        | IntegerField      | Total number of views across all dates.                           |

**Status choices:**

```python
class Status(models.TextChoices):
    DRAFT      = "DR"   # Private, owner-only
    PUBLISHED  = "PU"   # Public
    RESTRICTED = "RE"   # Password or login protected
    ENCODING   = "EN"   # Transcoding in progress
    ERROR      = "ER"   # Encoding failed
```

**License choices:** `CC-BY`, `CC-BY-SA`, `CC-BY-NC`, `CC-BY-ND`, `COPYRIGHT`.

**Key methods:**

- `thumbnail_url` _(property)_: Returns the thumbnail URL or the configured default.
- `get_dublin_core()`: Returns a Dublin Core metadata dictionary.
- `set_password()`: Hashes the password field using PBKDF2-SHA256 (idempotent).
- `save()`: Auto-generates the slug, hashes password, computes expiration date, and moves files on owner change.

---

### Subtitle

A subtitle file attached to a video (`src/apps/video/models/Subtitle.py`).

| Field        | Type         | Description                                           |
| :----------- | :----------- | :---------------------------------------------------- |
| `video`      | FK → Video   | Parent video.                                         |
| `language`   | CharField    | Language code: `fr`, `en`, or `es`.                   |
| `file`       | FileField    | Subtitle file (expected VTT/SRT). Path: `subtitles/`. |
| `is_default` | BooleanField | Marks this subtitle as the default track.             |

---

### VideoHyperlink

An interactive link displayed on top of the video during playback (`src/apps/video/models/VideoHyperlink.py`).

| Field        | Type         | Description                                          |
| :----------- | :----------- | :--------------------------------------------------- |
| `video`      | FK → Video   | Parent video.                                        |
| `text`       | CharField    | Display text for the link.                           |
| `url`        | URLField     | Target URL.                                          |
| `icon`       | CharField    | Name/class of the icon (e.g., `link`, `book`).       |
| `position`   | CharField    | Position on screen: `top-left`, `bottom-right`, etc. |
| `time_start` | IntegerField | Start time in seconds.                               |
| `time_end`   | IntegerField | End time in seconds.                                 |

---

### ViewCount

Stores daily view statistics per video (`src/apps/video/models/ViewCount.py`).

| Field   | Type                 | Description                           |
| :------ | :------------------- | :------------------------------------ |
| `video` | FK → Video           | Linked video.                         |
| `date`  | DateField            | Date of the views (unique per video). |
| `count` | PositiveIntegerField | Number of views on that date.         |

Unique constraint on `(video, date)`. Ordered by `-date`.

---

### Additional Models

- **Type (`src/apps/video/models/Type.py`)**: General categories for videos, filterable by `Site`.
- **Discipline (`src/apps/video/models/Discipline.py`)**: Formal academic categories.
- **Comment (`src/apps/video/models/Comment.py`)**: User remarks tied to a specific video with timestamp and user.
- **Vote (`src/apps/video/models/Vote.py`)**: Tracks Up/Down votes on `Comment` items to calculate the net score.
- **VideoCut (`src/apps/video/models/VideoCut.py`)**: Trimming definition (start/end in seconds) associated in a one-to-one relationship with a video.
- **Tag**: Handled dynamically by the `django-tagulous` extension.

---

## 2. Access Control & Permissions

### Visibility Logic (VideoViewSet.get_queryset)

The list of accessible videos depends on the user's authentication state:

- **Anonymous** — Published + Restricted (if `is_auth_required=False` and no `restricted_groups`).
  Password-protected videos may be hidden depending on `HOMEPAGE_SHOWS_PASSWORDED`.
- **Authenticated** — Published + Restricted + own videos (all statuses) + co-owned.
  Additionally, restricted videos limited to specific AccessGroups where the user is a member.
- **Superuser** — All videos without restriction.

### Permission Classes

**`IsOwnerOrCoOwnerOrReadOnly`** (`src/apps/video/permissions.py`):

- **Read** (`GET`, `HEAD`, `OPTIONS`): allowed for everyone.
- **Edit** (`PUT`, `PATCH`): owner, co-owner, or staff.
- **Delete** (`DELETE`): owner or staff only.
- If `RESTRICT_EDIT_TO_STAFF = True`: only staff/superusers can write.

**`IsSubtitleVideoOwnerOrReadOnly`** (inline in SubtitleViewSet):

- Read: allowed for all.
- Write/Delete: only the owner of the linked video.

**`HyperlinkViewSet` Permissions** (inline logic via `_check_video_permission`):

- Read: allowed for all.
- Write/Delete: restricted to the video's owner, co-owners, or owners of the linked channel/playlist. Rejects with 403 Forbidden otherwise.

---

## 3. Serializer (VideoSerializer)

Located in `src/apps/video/serializers/VideoSerializer.py`.

**Key behaviors:**

| Field          | Behavior                                                                            |
| :------------- | :---------------------------------------------------------------------------------- |
| `owner`        | Read-only — automatically set to `request.user` on create.                          |
| `slug`         | Read-only — auto-generated by the model.                                            |
| `video_file`   | Write-only — not exposed in GET responses.                                          |
| `video_url`    | Computed field — exposes the file URL based on permissions and `allow_downloading`. |
| `has_password` | Read-only boolean — indicates if the video is password-protected.                   |
| `password`     | Write-only — hashed via `validate_password` before save.                            |
| `subtitles`    | Nested read-only list of attached subtitles.                                        |

**File validations (`validate_video_file`):**

- Extension must be in `encoding_settings.allowed_extensions`.
- File size must not exceed `encoding_settings.max_upload_size_gb`.

**WEBTV Mode (`validate`):**

- If `WEBTV_MODE = False`: a video file is **mandatory**. A published video without a file is also rejected.

---

## 4. Signals

Located in `src/apps/video/signals.py`. Three signals are registered on the `Video` model:

| Signal                       | Trigger       | Action                                                                        |
| :--------------------------- | :------------ | :---------------------------------------------------------------------------- |
| `auto_delete_file_on_delete` | `post_delete` | Removes the physical files (video, thumbnail, overview) from disk.            |
| `auto_delete_file_on_change` | `pre_save`    | Deletes the old file when a new video file is uploaded.                       |
| `video_post_save`            | `post_save`   | On creation: extracts duration via `ffprobe`, leaves status as-is (ENCODING). |

> **Note:** The status transition to `PUBLISHED` is done by the Encoding webhook, not the signal.

---

## 5. Custom Actions (ViewSet)

### `GET /api/videos/{slug}/stream/`

Streams the raw video file. Access rules:

- Owner, co-owner, superuser: always allowed.
- Restricted + Group: Access limited to users in the assigned groups.
- Restricted + Password: direct stream blocked (use `/unlock/` first or supply valid legacy hash).
- Draft: blocked for non-owners.

### `POST /api/videos/{slug}/register_view/`

Atomically increments `view_count` on the video AND the daily `ViewCount` record. Returns the total count.

### `POST /api/videos/{slug}/unlock/`

Unlocks a password-protected restricted video.

- If `is_auth_required = True`: user must be authenticated.
- Validates the provided `password` against the stored hash. (Alternatively accepts a legacy `hash` parameter for backward compatibility).
- Returns the `video_url` on success and registers access in the session state.

### `PATCH|DELETE /api/videos/bulk/`

Applies an update or deletion to **multiple videos in one request**.

**Request body:**

```json
{
  "video_ids": [1, 2, 3],
  "fields": { "allow_downloading": true }
}
```

**Behaviour:**

- `PATCH`: updates only the fields listed in `fields`. Fields in `BULK_EXCLUDED_FIELDS`
  (`title`, `slug`, `owner`, `video_file`, `created_at`, `updated_at`, `duration`,
  `encoding_status`) are rejected with `400 Bad Request`.
- `DELETE`: deletes all listed videos. Returns `{ "deleted": N }`.
- **Async threshold**: if the number of selected videos exceeds `BULK_ASYNC_THRESHOLD`
  (default `20`, configurable), the operation is delegated to a Celery task and
  the response is `202 Accepted` with `{ "status": "queued" }`.
- **Permission check**: every video must be owned or co-owned by the requester.
  A `403 Forbidden` is raised on the first video that fails the check.
- **Feature flag**: returns `400` if `USE_BULK_ACTIONS = False`.

### `POST /api/cut/{slug}/` & `DELETE /api/cut/{slug}/delete/`

Manages the video cut feature (trimming a video virtually):

- **POST**: Creates or replaces a cut for the given video (payload: `time_start`, `time_end` in seconds). Automatically purges time-dependent objects (chapters, notes) attached to the video to avoid inconsistencies.
- **DELETE**: Removes the cut definition.
- **Permissions**: Requires owner, co-owner, or super-user rights. If `video_settings.restrict_edit_to_staff` is enabled, only staff members can manage cuts.

---

## 6. Upload & Encoding Flow

```text
1. POST /api/videos/       (multipart/form-data)
2. VideoViewSet.perform_create()
   ├── Quota check: current usage + file size vs. user_quota_size_gb
   ├── serializer.save(owner=user, status=ENCODING)
   └── trigger_runner_encoding_task.delay(video.pk, source_url)  [Celery]
3. Celery task contacts the Runner Manager API
4. Runner Manager encodes the video
5. POST /api/encoding/webhook/ (from Runner Manager)
   └── Video status → PUBLISHED (or ERROR)
```

---

## 7. Configuration Settings

Managed via `VideoConfig` (pydantic-settings in `src/apps/video/conf.py`). Settings are read from Django settings or environment variables with the prefix `POD_VIDEO_`.

| Setting                      | Default       | Description                                                 |
| :--------------------------- | :------------ | :---------------------------------------------------------- |
| `USE_HYPERLINKS`             | `True`        | Enables the video hyperlinks system globally.               |
| `WEBTV_MODE`                 | `False`       | If `True`, video file is optional (WebTV / channel mode).   |
| `ALLOW_AUTHENTICATED_UPLOAD` | `True`        | Allow authenticated non-staff users to upload.              |
| `RESTRICT_EDIT_TO_STAFF`     | `False`       | Locks write access to staff and admins only.                |
| `HOMEPAGE_SHOWS_PASSWORDED`  | `True`        | Show password-protected videos in public listing.           |
| `DEFAULT_LICENSE`            | `"COPYRIGHT"` | Default license applied to newly created videos.            |
| `DEFAULT_THUMBNAIL`          | (path)        | Path to the fallback thumbnail image.                       |
| `DEFAULT_YEAR_DATE_DELETE`   | `2`           | Default years before expiration (if no affiliation match).  |
| `ACCOMMODATION_YEARS`        | `{}`          | Dict mapping affiliation → nb years before deletion.        |
| `CACHE_TIMEOUT`              | `600`         | Cache TTL in seconds for video data.                        |
| `DEFAULT_DC_COVERAGE`        | (string)      | Dublin Core `coverage` metadata default.                    |
| `DEFAULT_DC_RIGHTS`          | (string)      | Dublin Core `rights` metadata default.                      |
| `USE_BULK_ACTIONS`           | `True`        | Enable bulk update/delete endpoint (`/api/videos/bulk/`).   |
| `BULK_ASYNC_THRESHOLD`       | `20`          | Videos above this count are processed async via Celery.     |

---

## 8. Testing

Run tests for the video application:

```bash
pytest src/apps/video/tests/
```

Key test files:

- `test_models.py`: Unit tests for Video, Subtitle, and ViewCount models.
- `test_views.py`: Integration tests for API endpoints (CRUD, stream, unlock, view counting).
- `test_hyperlinks.py`: Specific API test suite for the `VideoHyperlink` endpoints and permission checks.
- `test_scenarios.py`: End-to-end scenario tests (full upload → encoding → publish flow).
- `test_signals.py`: Tests for file cleanup signals.
- `test_bulk_actions.py`: Tests for the bulk update/delete endpoint (permissions, async, feature flag).

---

> **Pod V5 Team** | [Documentation Index](../README.md)

## Further Reading

- ⬅️ **[Back to Overview](README.md)**
- ⬅️ **[Back to Index](../README.md)**
