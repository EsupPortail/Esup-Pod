# Collection: Overview

The **Collection** application manages groups of videos through various container types: Channels, Themes, and Playlists. It provides the structural backbone for organizing content within Pod.

## Key Features

| Feature                    | Description                                                                     |
| :------------------------- | :------------------------------------------------------------------------------ |
| **Channels**               | Personal or institutional spaces for creators to group their content.           |
| **Themes**                 | Hierarchical taxonomy (categories) for global or channel-specific organization. |
| **Playlists**              | Ordered sequences of videos, optionally protected by password.                  |
| **Favorites**              | Personal bookmarks allowing users to keep track of videos they like.            |
| **Collaborators**          | Channels can have multiple managers with shared editing rights.                 |
| **Ordering**               | Drag-and-drop support for playlists with automatic rank calculation.            |
| **Hierarchical Integrity** | Prevents circular references and cross-channel nesting in theme hierarchies.    |
| **Thread-safety**          | Secure concurrent video additions to playlists using database locking.          |

## Collection Types

| Type         | Purpose                                                             | Visibility Options   |
| :----------- | :------------------------------------------------------------------ | :------------------- |
| **Channel**  | Institutional or individual portal. Acts as a root for themes.      | Public / Private     |
| **Theme**    | Academic or topical category. Supports infinite nesting.            | Inherited / Global   |
| **Playlist** | Curated list of videos (e.g., a specific course or lecture series). | Public / Password    |
| **Favorite** | Personal list of "liked" videos.                                    | Private (Owner only) |

## Core Logic

### Theme Hierarchy

Themes support a parent-child relationship. The system enforces two main rules:

1. **No Circularity**: A theme cannot be its own ancestor.
2. **Channel Isolation**: A sub-theme must belong to the same channel as its parent, or both must be global (no channel).

### Playlist Management

Playlists use a `through` model (`PlaylistItem`) to store videos with an associated `position`.

- **Auto-ranking**: When a video is added without a position, the system automatically assigns the next available rank (`MAX + 1`).
- **Atomic Operations**: Adding videos is performed inside a transaction with `select_for_update` to prevent race conditions.

## Data Models

| Model            | Role                                                               |
| :--------------- | :----------------------------------------------------------------- |
| **Channel**      | Container for themes and videos, with ownership and collaborators. |
| **Theme**        | Categorization model with hierarchy support.                       |
| **Playlist**     | Ordered list of videos with optional password protection.          |
| **Favorite**     | Simple link between a User and a Video.                            |
| **PlaylistItem** | Join model for Playlists, managing the `position` of each video.   |
| **ThemeItem**    | Join model for Themes, linking videos to categories.               |

## API Endpoints

| Method       | Endpoint                           | Description                                  |
| :----------- | :--------------------------------- | :------------------------------------------- |
| **GET**      | `/api/channels/`                   | List accessible channels.                    |
| **POST**     | `/api/channels/`                   | Create a new channel.                        |
| **GET**      | `/api/themes/`                     | List root themes (hierarchical navigation).  |
| **POST**     | `/api/themes/`                     | Create a new theme (admin or channel owner). |
| **GET**      | `/api/playlists/`                  | List public or owned playlists.              |
| **POST**     | `/api/playlists/{slug}/add_video/` | Add a video to a playlist (atomic).          |
| **POST**     | `/api/playlists/{slug}/reorder/`   | Bulk update video positions in a playlist.   |
| **GET/POST** | `/api/favorites/`                  | Manage personal favorite videos.             |

## Further Reading

- ➡️ **[Technical Details & Configuration](details.md)**: Models, permissions, hierarchy logic, and settings.
- ⬅️ **[Back to Index](../README.md)**
