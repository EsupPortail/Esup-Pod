# Collection: Technical Details

> **Navigation:** [Back to Overview](README.md) | [Back to Index](../README.md)

---

## 1. Models

### BaseContainer (Abstract)

All primary collection models (`Channel`, `Theme`, `Playlist`) inherit from `BaseContainer` (`src/apps/collection/models/base.py`).

| Field         | Type      | Description                                        |
| :------------ | :-------- | :------------------------------------------------- |
| `title`       | CharField | Display name (max 250).                            |
| `slug`        | SlugField | Unique URL identifier (auto-generated from title). |
| `description` | TextField | Full description (optional).                       |
| `old_v4_id`   | Integer   | Legacy ID for backward compatibility.              |
| `created_at`  | DateTime  | Creation timestamp.                                |
| `updated_at`  | DateTime  | Last update timestamp.                             |

---

### Channel

Represents a portal or a user-specific space (`src/apps/collection/models/Channel.py`).

| Field           | Type       | Description                                     |
| :-------------- | :--------- | :---------------------------------------------- |
| `owner`         | FK → User  | Primary owner and manager.                      |
| `is_public`     | Boolean    | If False, hidden from anonymous users.          |
| `image`         | ImageField | Channel logo/avatar.                            |
| `banner`        | ImageField | Large header image.                             |
| `collaborators` | M2M → User | Users with management rights (except deletion). |

---

### Theme

Hierarchical taxonomy for organizing videos (`src/apps/collection/models/Theme.py`).

| Field     | Type         | Description                                             |
| :-------- | :----------- | :------------------------------------------------------ |
| `channel` | FK → Channel | Optional link to a specific channel (private taxonomy). |
| `parent`  | FK → self    | Parent theme for nesting.                               |
| `videos`  | M2M → Video  | Associated videos (via `ThemeItem`).                    |

**Hierarchy Validation (`clean()`):**

- Prevents a theme from being its own parent.
- Prevents infinite loops in the ancestor tree.
- **Strict Isolation**: A sub-theme cannot belong to a different channel than its parent.

---

### Playlist

Curated and ordered lists of videos (`src/apps/collection/models/Playlist.py`).

| Field       | Type        | Description                                     |
| :---------- | :---------- | :---------------------------------------------- |
| `owner`     | FK → User   | Creator of the playlist.                        |
| `is_public` | Boolean     | Visibility toggle.                              |
| `password`  | CharField   | Optional hashed password for access protection. |
| `videos`    | M2M → Video | Ordered videos (via `PlaylistItem`).            |

**Ordering Logic (`PlaylistItem.save()`):**

- If no `position` is provided, the system calculates the next rank using `MAX(position) + 1` for the given playlist.

---

## 2. Access Control & Permissions

### Visibility Logic

- **Channels**:

- Public: Visible to all.
- Private: Visible to owner, collaborators, and staff.

- **Themes**:

- Global (no channel): Always visible.
- Channel-specific: Visibility inherited from the parent Channel.

- **Playlists**:

- Public: Visible to all.
- Private: Visible only to the owner.
- Password-protected: Visible if the correct password is provided (stored in session/headers).

### Custom Permissions

| Permission Class                         | Scope    | Rule                                                                  |
| :--------------------------------------- | :------- | :-------------------------------------------------------------------- |
| `IsOwnerOrReadOnly`                      | Playlist | Read for all (if public), Write/Delete for owner.                     |
| `IsChannelOwnerOrCollaboratorOrReadOnly` | Channel  | Read for public, Write for owner/collab, Delete for owner/staff.      |
| `IsAdminOrThemeOwner`                    | Theme    | Admin: Full access. Owner: Allowed if `OWNER_CAN_MANAGE_THEMES=True`. |

---

## 3. API Actions

### Playlist Reordering

`POST /api/playlists/{slug}/reorder/`
Accepts a list of `{"video_id": ID, "position": INT}` to bulk update the order.

### Password Verification

Password-protected playlists can be unlocked by:

1. Providing `?password=...` in the query string.
2. Providing `X-Playlist-Password` in the request headers.
   The `PlaylistViewSet.get_serializer_context` injects a `password_verified` flag used by the serializer to determine whether to expose items.

### Secure Serialization

Both `ThemeSerializer` and `PlaylistSerializer` filter their nested `items` to ensure that even if a video is linked to a collection, it is only returned if the current user has permission to see it (via `Video.objects.visible_for(user)`).

---

## 4. Configuration Settings

Managed via `CollectionConfig` (`src/apps/collection/conf.py`).

| Setting                     | Default | Description                                    |
| :-------------------------- | :------ | :--------------------------------------------- |
| `USE_CHANNELS`              | `True`  | Enable/disable the channel system.             |
| `OWNER_CAN_MANAGE_CHANNELS` | `True`  | Allow users to manage their own channels.      |
| `USE_CATEGORIES`            | `True`  | Enable the Theme/Taxonomy system.              |
| `OWNER_CAN_MANAGE_THEMES`   | `False` | Allow channel owners to create private themes. |
| `MAX_THEME_DEPTH`           | `3`     | Max depth for theme nesting.                   |
| `USE_PLAYLISTS`             | `True`  | Enable the playlist module.                    |
| `USE_PASSWORD_PROTECTION`   | `True`  | Allow passwords on playlists.                  |

---

## 5. Testing

Run tests for the collection application:

```bash
pytest src/apps/collection/tests/
```

Key test files:

- `test_collections.py`: Tests for Channel, Theme, and Playlist CRUD and permissions.

---

> **Pod V5 Team** | [Documentation Index](../README.md)

## Further Reading

- ⬅️ **[Back to Overview](README.md)**
- ⬅️ **[Back to Index](../README.md)**
