# Encoding: Overview

The Pod application encoding module handles asynchronous video transcoding and processing through a distributed task queue system. It communicates with an external **Esup-Runner Manager** service to perform encoding operations on videos.

## Architecture

The encoding system is built on three key components:

| Component              | Role                                                                              |
| :--------------------- | :-------------------------------------------------------------------------------- |
| **Pod Backend**        | Triggers encoding tasks via Celery and stores metadata in the database.           |
| **Celery + Redis**     | Manages the asynchronous task queue and handles retries for failed encoding jobs. |
| **Runner Manager API** | External microservice that performs the actual video transcoding and processing.  |

## How It Works

1. **Task Trigger**: When a video is uploaded, `VideoViewSet.perform_create()` calls `trigger_runner_encoding_task.delay(video_id, source_url)`.
2. **Queue**: The task is queued in Redis (Celery broker) for asynchronous execution.
3. **Execution**: Celery picks up the task and communicates with the Runner Manager API (`POST /task/execute`).
4. **Processing**: Runner Manager encodes the video into multiple formats (360p, 480p, 720p, 1080p, audio, playlist).
5. **Webhook**: Runner Manager notifies Pod (`POST /api/encoding/webhook/`) when encoding is complete.
6. **Retry Logic**: If encoding fails due to a **network error**, Celery automatically retries up to 3 times with 60-second delays. Other errors immediately set the video to `ERROR`.

## Supported Encoding Formats

Pod can encode videos into the following outputs:

| Format       | Description                         |
| :----------- | :---------------------------------- |
| **audio**    | MP3 audio file                      |
| **360p**     | 360p video resolution (low quality) |
| **480p**     | 480p video resolution (standard)    |
| **720p**     | 720p video resolution (HD)          |
| **1080p**    | 1080p video resolution (Full HD)    |
| **playlist** | HLS playlist for adaptive streaming |

## Key Technologies

- **Celery**: Asynchronous task queue for job distribution
- **Redis**: Message broker for Celery and distributed caching
- **FFmpeg/FFprobe**: Video analysis and encoding tools (via Runner Manager)
- **Pydantic**: Configuration management with type validation

## API Endpoints

| Method   | Endpoint                 | Description                                                    |
| :------- | :----------------------- | :------------------------------------------------------------- |
| **POST** | `/api/encoding/webhook/` | Receives encoding completion notification from Runner Manager. |

> The webhook endpoint is public but secured by the `ENCODING_WEBHOOK_SECRET` environment variable via the `X-Webhook-Secret` header.

## File Storage

Video-related files are organized on disk using a hash-based directory strategy to obscure physical files and avoid predictable names.

```text
MEDIA_ROOT/
├── video/
│   ├── source/
│   │   └── %Y/%m/%d/<hash>.mp4
│   ├── encoded/
│   │   └── %Y/%m/%d/<hash>.mp4
│   ├── thumbnails/
│   │   └── %Y/%m/%d/<hash>.jpg
│   └── transcripts/
│       └── %Y/%m/%d/<hash>.vtt
└── userpicture/
    └── %Y/%m/%d/<hash>.jpg
```

## Further Reading

- ➡️ **[Technical Details & Configuration](details.md)**: Environment variables, API integration, webhook payload, and advanced setup.
- ⬅️ **[Back to Index](../README.md)**
