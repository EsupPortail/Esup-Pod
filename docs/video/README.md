<!-- markdownlint-disable MD013 -->
# Video: Overview

The **Video** application is the core module of Pod V5. It manages the full lifecycle of video content — from upload and metadata management to access control and streaming.

## Key Features

| Feature                | Description                                                                        |
| :--------------------- | :--------------------------------------------------------------------------------- |
| **Video Upload**       | Supports multiple formats (mp4, avi, mov, mkv, webm…) with quota enforcement.      |
| **Access Control**     | Fine-grained visibility: Public, Draft, Restricted (by password and/or login).     |
| **Co-ownership**       | Multiple users can share edit rights on the same video.                            |
| **Subtitles**          | Attach subtitle files (VTT/SRT) per language (FR, EN, ES).                         |
| **Streaming**          | Direct file streaming via a dedicated API endpoint.                                |
| **Video Duplication**  | Duplicate a video completely (ISO V4: copies files, metadata, links).              |
| **Video Cut**          | Trim a video virtually using a start and end time (clears chapters/notes).         |
| **Marker Time**        | Automatically saves and retrieves the user's video playback position.              |
| **Hyperlinks**         | Add interactive links (timecodes, external resources) to videos.                   |
| **Completion Data**    | Contributions, overlays, and documents are embedded in the video response.         |
| **Categorization**     | Organize videos with Types, Disciplines, and Tags.                                 |
| **Comments & Votes**   | Engage users with a commenting and upvote/downvote system.                         |
| **Multi-tenancy**      | Videos are linked to specific Sites (portals) for data isolation.                  |
| **Legacy Support**     | Backward compatibility with V4 URLs and legacy password hashes.                    |
| **View Tracking**      | Daily view count per video, accessible via the API.                                |
| **Auto-expiration**    | Deletion date computed automatically based on the owner's affiliation.             |
| **Encoding Pipeline**  | On upload, triggers an asynchronous encoding task via the Encoding app.            |
| **Bulk Actions**       | Update or delete multiple videos in one request (async via Celery above threshold). |

## Video Status Lifecycle

A video passes through the following states:

```text
[Upload / Create] → ENCODING → (webhook from Runner) → PUBLISHED
                                                      ↘ ERROR
                    (manual) → DRAFT
                    (manual) → RESTRICTED
```

| Status         | Code | Description                                         |
| :------------- | :--- | :-------------------------------------------------- |
| **Encoding**   | `EN` | Transcoding in progress (default after upload).     |
| **Published**  | `PU` | Public — visible to all users.                      |
| **Draft**      | `DR` | Private — only visible to the owner.                |
| **Restricted** | `RE` | Access controlled (password and/or login required). |
| **Error**      | `ER` | Encoding failed.                                    |

## Data Models

| Model              | Role                                                                         |
| :----------------- | :--------------------------------------------------------------------------- |
| **Video**          | Central model containing all metadata, access settings, and site isolation.  |
| **Type**           | General categorization type for videos.                                      |
| **Discipline**     | Academic disciplines associated with videos.                                 |
| **Tag**            | Free-form tags for better searchability.                                     |
| **Comment**        | User comments left on a video.                                               |
| **Vote**           | Upvotes and downvotes for comments.                                          |
| **Subtitle**       | A subtitle file attached to a video, for a given language.                   |
| **VideoCut**       | Trimming definition (start/end in seconds) associated with a video.          |
| **VideoHyperlink** | Interactive links attached to a video at specific time intervals.            |
| **ViewCount**      | Stores the number of views per day, per video.                               |

## API Endpoints

| Method       | Endpoint                              | Description                                       |
| :----------- | :------------------------------------ | :------------------------------------------------ |
| **GET**      | `/api/videos/`                        | List accessible videos.                           |
| **POST**     | `/api/videos/`                        | Upload a new video (multipart/form-data).         |
| **GET**      | `/api/videos/{slug}/`                 | Retrieve a single video's details.                |
| **PATCH**    | `/api/videos/{slug}/`                 | Update a video (owner/co-owner only).             |
| **DELETE**   | `/api/videos/{slug}/`                 | Delete a video (owner/admin only).                |
| **GET**      | `/api/videos/{slug}/stream/`          | Stream the video file directly.                   |
| **POST**     | `/api/videos/{slug}/duplicate/`       | Duplicate the video completely (files & metadata).|
| **POST**     | `/api/videos/{slug}/register_view/`   | Increment the view counter.                       |
| **POST**     | `/api/videos/{slug}/unlock/`          | Unlock a password-protected restricted video.     |
| **GET**      | `/api/types/`                         | List available video types.                       |
| **GET**      | `/api/disciplines/`                   | List available disciplines.                       |
| **GET**      | `/api/tags/`                          | List available tags.                              |
| **GET/POST** | `/api/videos/{slug}/comments/`        | Manage comments for a video.                      |
| **POST/DEL** | `/api/comments/{id}/vote/`            | Upvote/downvote or remove vote on a comment.      |
| **GET**      | `/api/hyperlinks/`                    | List video hyperlinks.                            |
| **POST**     | `/api/cut/{slug}/`                    | Create or replace a video cut.                    |
| **DELETE**   | `/api/cut/{slug}/delete/`             | Delete the cut associated with the video.         |
| **POST**     | `/api/hyperlinks/`                    | Create a hyperlink (video owner/co-owner only).   |
| **PATCH/DEL**| `/api/hyperlinks/{id}/`               | Modify or delete a hyperlink.                     |
| **GET**      | `/api/subtitles/`                     | List subtitles (filterable by `?video_id=`).      |
| **POST**     | `/api/subtitles/`                     | Attach a subtitle to a video.                     |
| **DELETE**   | `/api/subtitles/{id}/`                | Delete a subtitle (video owner only).             |
| **PATCH**    | `/api/videos/bulk/`                   | Bulk update fields on multiple videos.            |
| **DELETE**   | `/api/videos/bulk/`                   | Bulk delete multiple videos.                      |
| **GET**      | `/api/marker/{video_slug}/`           | Retrieve the playback position for the user.      |
| **POST**     | `/api/marker/{video_slug}/save/`      | Save the playback position for the user.          |
| **DELETE**   | `/api/marker/{video_slug}/reset/`     | Delete the playback position marker.              |

> **Note:** Completion data (contributions, overlays, documents) is automatically embedded in the `GET /api/videos/{slug}/` and `GET /api/videos/` responses. To create or modify these elements, use the dedicated [`/api/completion/`](../completion/README.md) endpoints.

## Further Reading

- ➡️ **[Technical Details & Configuration](details.md)**: Models, signals, permissions, serializer behavior, and settings.
- ⬅️ **[Back to Index](../README.md)**
