# Completion: Overview

The **Completion** application extends the Esup-Pod video ecosystem by providing advanced metadata, documents, overlays, and automated enrichment capabilities.

## Key Features

| Feature           | Description                                                                     |
| :---------------- | :------------------------------------------------------------------------------ |
| **Documents**     | Attach additional documents (PDFs, slides, etc.) directly to a video.           |
| **Contributors**  | Manage individuals (speakers, directors, etc.) involved in video production.    |
| **Contributions** | Link contributors to specific videos with distinct roles (actor, author, etc.). |
| **Overlays**      | Add contextual time-based overlays (pop-ups, links) on top of the video player. |

## Data Models

| Model            | Role                                                                                  |
| :--------------- | :------------------------------------------------------------------------------------ |
| **Contributor**  | Represents an individual (name, email, organization) participating in a video.        |
| **Contribution** | Association between a Video and a Contributor, including the specific role.           |
| **Document**     | An auxiliary file attached to a video for viewers to download.                        |
| **Overlay**      | Content displayed at specific timestamps (`time_start` to `time_end`) over the video. |

## API Endpoints

| Method   | Endpoint              | Description                                        |
| :------- | :-------------------- | :------------------------------------------------- |
| **GET**  | `/api/contributors/`  | List all contributors (filterable).                |
| **POST** | `/api/contributors/`  | Create a new contributor profile.                  |
| **GET**  | `/api/contributions/` | List video contributions (filterable by video_id). |
| **POST** | `/api/contributions/` | Add a new contribution to a video.                 |
| **GET**  | `/api/documents/`     | List attached documents (filterable by video_id).  |
| **POST** | `/api/documents/`     | Upload a document to a video.                      |
| **GET**  | `/api/overlays/`      | List overlays for videos (filterable by video_id). |
| **POST** | `/api/overlays/`      | Create a new time-based overlay for a video.       |

## Further Reading

- ➡️ **[Technical Details & Configuration](details.md)**: Models, signals, permissions, serializer behavior, and settings.
- ⬅️ **[Back to Index](../README.md)**
