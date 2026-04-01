# Video: Overview

The **Video** application is the core module of Pod V5. It manages the full lifecycle of video content — from upload and metadata management to access control and streaming.

## Key Features

| Feature                | Description                                                                        |
| :--------------------- | :--------------------------------------------------------------------------------- |
| **Video Upload**       | Supports multiple formats (mp4, avi, mov, mkv, webm…) with quota enforcement.    |
| **Access Control**     | Fine-grained visibility: Public, Draft, Restricted (by password and/or login).   |
| **Co-ownership**       | Multiple users can share edit rights on the same video.                            |
| **Subtitles**          | Attach subtitle files (VTT/SRT) per language (FR, EN, ES).                        |
| **Streaming**          | Direct file streaming via a dedicated API endpoint.                                |
| **Categorization**     | Organize videos with Types, Disciplines, and Tags.                                 |
| **Comments & Votes**   | Engage users with a commenting and upvote/downvote system.                         |
| **Multi-tenancy**      | Videos are linked to specific Sites (portals) for data isolation.                  |
| **Legacy Support**     | Backward compatibility with V4 URLs and legacy password hashes.                    |
| **View Tracking**      | Daily view count per video, accessible via the API.                                |
| **Auto-expiration**    | Deletion date computed automatically based on the owner's affiliation.            |
| **Encoding Pipeline**  | On upload, triggers an asynchronous encoding task via the Encoding app.            |

## Video Status Lifecycle

A video passes through the following states:

```
[Upload / Create] → ENCODING → (webhook from Runner) → PUBLISHED
                                                      ↘ ERROR
                    (manual) → DRAFT
                    (manual) → RESTRICTED
```

| Status          | Code | Description                                         |
| :-------------- | :--- | :-------------------------------------------------- |
| **Encoding**    | `EN` | Transcoding in progress (default after upload).     |
| **Published**   | `PU` | Public — visible to all users.                      |
| **Draft**       | `DR` | Private — only visible to the owner.                |
| **Restricted**  | `RE` | Access controlled (password and/or login required). |
| **Error**       | `ER` | Encoding failed.                                    |

## Data Models

| Model         | Role                                                        |
| :------------ | :---------------------------------------------------------- |
| **Video**     | Central model containing all metadata, access settings, and site isolation. |
| **Type**      | General categorization type for videos.                                     |
| **Discipline**| Academic disciplines associated with videos.                                |
| **Tag**       | Free-form tags for better searchability.                                    |
| **Comment**   | User comments left on a video.                                              |
| **Vote**      | Upvotes and downvotes for comments.                                         |
| **Subtitle**  | A subtitle file attached to a video, for a given language.                  |
| **ViewCount** | Stores the number of views per day, per video.                              |

## API Endpoints

| Method     | Endpoint                              | Description                                       |
| :--------- | :------------------------------------ | :------------------------------------------------ |
| **GET**    | `/api/videos/`                        | List accessible videos.                           |
| **POST**   | `/api/videos/`                        | Upload a new video (multipart/form-data).         |
| **GET**    | `/api/videos/{slug}/`                 | Retrieve a single video's details.                |
| **PATCH**  | `/api/videos/{slug}/`                 | Update a video (owner/co-owner only).             |
| **DELETE** | `/api/videos/{slug}/`                 | Delete a video (owner/admin only).                |
| **GET**    | `/api/videos/{slug}/stream/`          | Stream the video file directly.                   |
| **POST**   | `/api/videos/{slug}/register_view/`   | Increment the view counter.                       |
| **POST**   | `/api/videos/{slug}/unlock/`          | Unlock a password-protected restricted video.     |
| **GET**    | `/api/types/`                         | List available video types.                       |
| **GET**    | `/api/disciplines/`                   | List available disciplines.                       |
| **GET**    | `/api/tags/`                          | List available tags.                              |
| **GET/POST** | `/api/videos/{slug}/comments/`      | Manage comments for a video.                      |
| **POST/DEL** | `/api/comments/{id}/vote/`          | Upvote/downvote or remove vote on a comment.      |
| **GET**    | `/api/subtitles/`                     | List subtitles (filterable by `?video_id=`).      |
| **POST**   | `/api/subtitles/`                     | Attach a subtitle to a video.                     |
| **DELETE** | `/api/subtitles/{id}/`                | Delete a subtitle (video owner only).             |

## Further Reading

- ➡️ **[Technical Details & Configuration](details.md)**: Models, signals, permissions, serializer behavior, and settings.
- ⬅️ **[Back to Index](../README.md)**
