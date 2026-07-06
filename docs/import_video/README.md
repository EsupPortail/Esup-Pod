<!-- markdownlint-disable MD013 MD060 -->
# Import Video: Overview

The **Import Video** application enables staff users to declare external video sources and import them directly into Pod V5. It supports multiple platforms and triggers the standard encoding pipeline on success.

## Key Features

| Feature                  | Description                                                                        |
| :----------------------- | :--------------------------------------------------------------------------------- |
| **Multi-source Support** | Import from YouTube, PeerTube, BigBlueButton, Mediacad, or direct video file URLs. |
| **Async Import**         | Import is processed asynchronously via Celery — no blocking HTTP requests.         |
| **Status Tracking**      | Real-time import status (`PENDING`, `PROCESSING`, `DONE`, `ERROR`).                |
| **Error Reporting**      | Detailed error messages stored on the recording for debugging.                     |
| **Encoding Integration** | On success, triggers the standard Esup-Runner encoding pipeline.                   |
| **Staff Restriction**    | Import can be restricted to staff users via configuration.                         |
| **Reset & Retry**        | Failed imports can be reset and retried via a dedicated API action.                |

## Supported Source Types

| Type              | Engine                        | Status         |
| :---------------- | :---------------------------- | :------------- |
| **YouTube**       | `yt-dlp`                      | ✅ Implemented  |
| **PeerTube**      | PeerTube REST API             | ✅ Implemented  |
| **BigBlueButton** | HTML parsing (standard only)  | ✅ Implemented  |
| **BBB ESR**       | Meeting module (not migrated) | ⏳ Pending      |
| **Video File**    | Direct URL download           | ✅ Implemented  |
| **Mediacad**      | Mediacad JSON API             | ✅ Implemented  |

## Import Status Lifecycle

```text
[Create Recording] → PENDING
                       ↓ (POST /import)
                     PROCESSING
                       ↓
              ┌── DONE (Video created + encoding triggered)
              └── ERROR (error_message populated)
                       ↓ (POST /reset)
                     PENDING  (retry)
```

## Data Models

| Model                 | Role                                                                      |
| :-------------------- | :------------------------------------------------------------------------ |
| **ExternalRecording** | Stores the external source declaration, import status, and linked Video.  |

## API Endpoints

| Method    | Endpoint                                    | Description                                           |
| :-------- | :------------------------------------------ | :---------------------------------------------------- |
| **GET**   | `/api/external-recordings/`                 | List recordings owned by the current user.            |
| **POST**  | `/api/external-recordings/`                 | Declare a new external recording.                     |
| **GET**   | `/api/external-recordings/{id}/`            | Retrieve a single recording's details and status.     |
| **PATCH** | `/api/external-recordings/{id}/`            | Update a recording (owner only).                      |
| **DELETE**| `/api/external-recordings/{id}/`            | Delete a recording (owner only).                      |
| **POST**  | `/api/external-recordings/{id}/import/`     | Trigger async import to Pod (returns 202 Accepted).   |
| **POST**  | `/api/external-recordings/{id}/reset/`      | Reset import status to PENDING for retry.             |

## Further Reading

- ➡️ **[Technical Details & Configuration](details.md)**: Models, services, permissions, tasks, and settings.
- ⬅️ **[Back to Index](../README.md)**
