# Notes: Technical Details

>
> **Navigation:** [Back to Overview](README.md) | [Back to Index](../README.md)

---

## 1. Models

### VideoNote

Stores a user note attached to a video (`src/apps/notes/models/VideoNote.py`).

| Field        | Type                | Description                                                        |
| :----------- | :------------------ | :----------------------------------------------------------------- |
| `video`      | FK → Video          | The video the note is attached to.                                 |
| `owner`      | FK → User           | The user who created the note.                                     |
| `content`    | TextField           | The note content.                                                  |
| `timestamp`  | PositiveIntegerField| Optional video time in seconds. Null for global notes.             |
| `privacy`    | CharField (choices) | Privacy level: `private` or `public`.                              |
| `created_at` | DateTimeField       | Creation timestamp (auto).                                         |
| `updated_at` | DateTimeField       | Last update timestamp (auto).                                      |

**PrivacyStatus choices:**

```python
class PrivacyStatus(models.TextChoices):
    PRIVATE = "private"  # Only visible to the owner
    PUBLIC  = "public"   # Visible to all users with video access
```

**Ordering:** Notes are ordered by `timestamp` then `created_at`.

---

## 2. Access Control & Permissions

### `IsNoteOwner` (`src/apps/notes/permissions.py`)

| Method             | Rule                                     |
| :----------------- | :--------------------------------------- |
| Safe (`GET`)       | Any authenticated user.                  |
| Write (`PATCH`)    | Owner only.                              |
| Delete (`DELETE`)  | Owner only.                              |

### Visibility Logic (`get_queryset`)

Notes are filtered using:

```python
Q(privacy=VideoNote.PrivacyStatus.PUBLIC) | Q(owner=request.user)
```

Private notes are **never** returned to other users — they receive a 404 if they attempt to access one directly.

### Video Access Check (`perform_create`)

Before creating a note, the viewset verifies that the target video is visible to the current user via `Video.objects.visible_for(user)`. A 403 is raised if the user has no access to the video.

---

## 3. Serializer

Located in `src/apps/notes/serializers/VideoNoteSerializer.py`.

| Field           | Behavior                                                        |
| :-------------- | :-------------------------------------------------------------- |
| `owner`         | Read-only — automatically set to `request.user` on create.     |
| `privacy_label` | Read-only — human-readable privacy status.                      |
| `timestamp`     | Optional — validated to be positive if provided.                |

---

## 4. Configuration Settings

Managed via `NotesConfig` (`src/apps/notes/conf.py`). Defaults in `src/config/defaults/notes.py`.

| Setting      | Default | Description                              |
| :----------- | :------ | :--------------------------------------- |
| `USE_NOTES`  | `True`  | Enable/disable the notes feature entirely.|

---

## 5. Testing

Run tests for the notes application:

```bash
pytest src/apps/notes/tests/
```

Key test files:

- `test_notes.py`: Tests for VideoNote model, CRUD operations, privacy filtering, and permission checks.

---

> **Pod V5 Team** | [Documentation Index](../README.md)

## Further Reading

- ⬅️ **[Back to Overview](README.md)**
- ⬅️ **[Back to Index](../README.md)**