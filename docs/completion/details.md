# Completion: Technical Details

>
> **Navigation:** [Back to Overview](README.md) | [Back to Index](../README.md)

---

## 1. Models

### Contributor

Represents a person participating in a video (`src/apps/completion/models/Contributor.py`).

| Field               | Type              | Description                                                       |
| :------------------ | :---------------- | :---------------------------------------------------------------- |
| `first_name`        | CharField         | First name of the contributor.                                    |
| `last_name`         | CharField         | Last name of the contributor.                                     |
| `email_address`     | EmailField        | Email address (optional).                                         |

### Contribution

Links a `Contributor` to a `Video` with a specific role (`src/apps/completion/models/Contribution.py`).

| Field         | Type             | Description                                                          |
| :------------ | :--------------- | :------------------------------------------------------------------- |
| `video`       | FK → Video       | Parent video.                                                        |
| `contributor` | FK → Contributor | The linked individual.                                               |
| `role`        | CharField        | The role (e.g., actor, author, director). Defined in `ROLE_CHOICES`. |

### Document

A supplementary file attached to a video (`src/apps/completion/models/Document.py`).

| Field   | Type       | Description                                                 |
| :------ | :--------- | :---------------------------------------------------------- |
| `video` | FK → Video | Linked video.                                               |
| `title` | CharField  | Title of the document.                                      |
| `file`  | FileField  | The physical file. Path: `documents/<year>/<month>/<day>/`. |

### Overlay

A time-bound pop-up or textual overlay displayed over the video player (`src/apps/completion/models/Overlay.py`).

| Field        | Type         | Description                                            |
| :----------- | :----------- | :----------------------------------------------------- |
| `video`      | FK → Video   | Parent video.                                          |
| `title`      | CharField    | Short title of the overlay.                            |
| `content`    | TextField    | Text or HTML content to display.                       |
| `time_start` | IntegerField | Start time in seconds.                                 |
| `time_end`   | IntegerField | End time in seconds. Must be > `time_start`.           |

*Validation:* The `clean` and `save` methods ensure `time_end` is strictly greater than `time_start`. If `LINK_SUPERPOSITION` is enabled in the configuration, URLs within `content` are automatically converted to HTML links.

---

## 2. Access Control & Permissions

### `CanManageContribution` (`src/apps/completion/permissions.py`)

- **Read** (`GET`, `HEAD`, `OPTIONS`): allowed for all authenticated users (or based on general read permissions).
- **Edit/Delete** (`PUT`, `PATCH`, `DELETE`): only the owner of the `Video` linked to the object (e.g., Document, Overlay, Contribution) is permitted to modify it. Superusers are also allowed.

---

## 3. Serializers

Located in `src/apps/completion/serializers/`.

- **`OverlaySerializer`**: Handles automatic URL-to-HTML-link conversion based on the `LINK_SUPERPOSITION` setting during `validate_content`. Also enforces `time_start < time_end`.
- **`DocumentSerializer`**: Includes validation to ensure the linked video has proper ownership for the uploading user.

---

## 4. Configuration Settings

Managed via `CompletionConfig` (pydantic-settings in `src/apps/completion/conf.py`).

| Setting                      | Default       | Description                                                 |
| :--------------------------- | :------------ | :---------------------------------------------------------- |
| `ROLE_CHOICES`               | (tuple)       | Available roles for contributors.                           |
| `KIND_CHOICES`               | (tuple)       | Available kinds for subtitle tracks.                        |
| `DEFAULT_LANG_TRACK`         | `"fr"`        | Default language for new subtitle tracks.                   |
| `LINK_SUPERPOSITION`         | `False`       | Enable automatic conversion of URLs into links in overlays. |
| `USE_SPEAKER`                | `False`       | Enable or disable the Speakers module.                      |
| `REQUIRED_SPEAKER_FIRSTNAME` | `True`        | Make the first name of a speaker mandatory.                 |

---

## 5. Integration with Video API

Contributions, overlays, and documents are **automatically embedded** in the `VideoSerializer` response (read-only nested fields). This means:

- A single `GET /api/videos/{slug}/` request returns all completion data for the player.
- The `VideoViewSet.get_queryset()` uses `prefetch_related("contributions__contributor", "overlays", "documents")` to prevent N+1 query issues on list endpoints.
- **Writing** completion data (creating/editing contributions, documents, overlays) is done via the dedicated `/api/completion/` endpoints — not through `PATCH /api/videos/`.

---

## 6. Testing

Run tests for the completion application:

```bash
pytest src/apps/completion/tests/
```

Key test files:

- `test_models.py`: Unit tests for models (validation, logic).
- `test_serializers.py`: Tests for specific validation (time checking, URL conversion).
- `test_permissions.py`: Ensures only video owners can modify related completion objects.

---

> **Pod V5 Team** | [Documentation Index](../README.md)

## Further Reading

- ⬅️ **[Back to Overview](README.md)**
- ⬅️ **[Back to Index](../README.md)**
