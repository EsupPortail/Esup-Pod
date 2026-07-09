# Encoding: Technical Details & Configuration

> **Navigation:** [Back to Overview](README.md) | [Back to Index](../README.md)

---

## Environment Variables

Configure the encoding module via environment variables in `.env`:

### Runner Manager Connection

```bash
# URL of the Esup-Runner Manager API
ENCODING_MANAGER_URL=http://runner-manager:8080
# API token for authentication with Runner Manager
ENCODING_MANAGER_TOKEN=your-secret-token
# Shared secret used to validate incoming webhook calls from Runner Manager
ENCODING_WEBHOOK_SECRET=your-webhook-secret
```

### Storage Configuration

```bash
# Default directory for video uploads (relative to MEDIA_ROOT)
POD_ENCODING_VIDEOS_DIR=videos
# Default directory for video thumbnails (relative to MEDIA_ROOT)
POD_ENCODING_THUMBNAILS_DIR=thumbnails
```

### Upload Configuration

```bash
# Maximum video upload size in GB (default: 10)
POD_ENCODING_MAX_UPLOAD_SIZE_GB=10
# Allowed video file extensions (comma-separated)
# Default: mp4,avi,mov,mkv,flv,webm,m4v,m2ts,mts,ts,mpg,ogg,mp3
POD_ENCODING_ALLOWED_EXTENSIONS=mp4,avi,mov,mkv,flv,webm,m4v,m2ts,mts,ts,mpg,ogg,mp3
```

### Quota Configuration

```bash
# Maximum disk space per user in GB (default: 100)
POD_ENCODING_USER_QUOTA_SIZE_GB=100
```

### Required Video Fields

```bash
# Comma-separated list of required fields when uploading a video
# Default: title,source_file,owner
POD_ENCODING_VIDEO_REQUIRED_FIELDS=title,source_file,owner
```

## Celery & Redis Configuration

Encoding relies on Celery for asynchronous task management:

```python
# src/config/django/base.py
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"
```

These use **Redis database 0** for task queuing. Other Redis databases are used for caching:

- **DB 0**: Celery broker and results
- **DB 1**: General cache (default)
- **DB 2**: Select2 library cache
- **DB 3**: Session data
- **DB 4**: Reserved for future use

## Encoding Task Flow

### Triggering Encoding

```python
from src.apps.encoding.tasks import trigger_runner_encoding_task
# Asynchronously trigger encoding for a video
trigger_runner_encoding_task.delay(
    video_id=123,
    source_url="https://example.org/video.mp4"
)
```

### Task Implementation

The encoding task is defined in `src/apps/encoding/tasks.py`:

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def trigger_runner_encoding_task(self, video_id: int, source_url: str):
    """
    Triggers an encoding task on the runner manager for a given video.
    - Retries up to 3 times on failure
    - 60-second delay between retries
    - Marks video as ERROR if all retries fail
    """
```

### Runner Manager API Integration

Pod communicates with the Runner Manager via the `RunnerClient` class:

```python
from src.apps.encoding.services.runner_client import get_runner_client
client = get_runner_client()
response = client.execute_task(
    video_id="video-slug",
    source_url="https://example.org/video.mp4",
    parameters={
        "video_id": 123,
        "slug": "video-slug",
        "title": "My Video",
        "encoding_choices": ["360p", "720p", "1080p", "audio", "playlist"]
    }
)
```

**Request Payload Example:**

```json
{
  "etab_name": "Pod",
  "app_name": "Pod",
  "app_version": "5.0.0",
  "task_type": "encoding",
  "source_url": "https://example.org/video.mp4",
  "notify_url": "https://pod.example.org/api/encoding/webhook/",
  "parameters": {
    "video_id": 123,
    "slug": "video-slug",
    "title": "My Video",
    "encoding_choices": ["360p", "720p", "1080p", "audio", "playlist"]
  }
}
```

## Retry Strategy

The Celery task implements an exponential backoff retry strategy:

| Attempt | Delay | Total Time |
| :------ | :---- | :--------- |
| 1st     | 0s    | 0s         |
| 2nd     | 60s   | 60s        |
| 3rd     | 60s   | 120s       |
| 4th     | 60s   | 180s       |

After 3 failed retries (total time: ~3 minutes), the video status is set to `ERROR`.

## Webhook: Encoding Completion Notification

The Runner Manager notifies Pod when encoding is done via **POST** `/api/encoding/webhook/`.

### Security

The endpoint is public but guarded by a shared secret:

```text
X-Webhook-Secret: <value of ENCODING_WEBHOOK_SECRET>
```

If `ENCODING_WEBHOOK_SECRET` is set and the header does not match, the request is rejected with `401 Unauthorized`.

### Payload — Success

```json
{
  "status": "success",
  "video_id": "123",
  "duration": "142.5",
  "results": {
    "overview_path": "video/thumbnails/2026/03/18/abc123.jpg",
    "output_video_360p": "video/encoded/2026/03/18/360.mp4",
    "output_video_720p": "video/encoded/2026/03/18/720.mp4"
  }
}
```

→ Video status is set to `PUBLISHED`. Duration and `overview` paths are updated on the `Video` model.
→ For every output video resolution returned (e.g. `output_video_360p`), an `EncodingVideo` record is created to store the resolution name and file path for the multi-format streaming player.

### Payload — Error

```json
{
  "status": "error",
  "video_id": "123",
  "error": "FFmpeg process failed"
}
```

→ Video status is set to `ERROR`.

---

## Testing

Run encoding tests with:

```bash
pytest src/apps/encoding/tests/
```

Key test files:

- `test_tasks.py`: Tests for Celery task triggering and retry logic
- `test_webhook.py`: Tests for webhook endpoint that receives encoding completion notifications

## Monitoring & Debugging

### View Celery Tasks

Monitor active and pending tasks:

```bash
# Connect to Celery worker
celery -A src.main inspect active
# View pending tasks
celery -A src.main inspect reserved
# Monitor in real-time
celery -A src.main events
```

### View Redis Queue

Check Redis for queued tasks:

```bash
redis-cli
> SELECT 0
> KEYS *
> HGETALL celery-task-meta-{task-id}
```

### Logs

Encoding logs are written to:

- **Logger name**: `src.apps.encoding`
- **File**: Check Django logging configuration

Common log messages:

```text
INFO: Triggering encoding task for video 123
INFO: Runner manager accepted task for video 123. Response: {...}
ERROR: Failed to trigger encoding for video 123: ConnectionError
ERROR: Runner manager response: {"error": "Invalid API token"}
```

## Configuration in Production

For production deployments with Docker Compose:

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  celery:
    image: pod:latest
    command: celery -A src.main worker --loglevel=info
    environment:
      - DJANGO_SETTINGS_MODULE=src.config.django.prod.docker
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
  pod:
    image: pod:latest
    environment:
      - POD_ENCODING_MANAGER_URL=http://runner-manager:8080
      - POD_ENCODING_MANAGER_TOKEN=${ENCODING_TOKEN}
    depends_on:
      - redis
      - celery
```

## Common Issues & Solutions

### Redis Connection Error

**Symptom**: `ConnectionError: Cannot connect to redis://redis:6379/0`

**Solution**:

- Verify Redis is running: `redis-cli ping` should return `PONG`
- Check `CELERY_BROKER_URL` environment variable
- Ensure Redis container network is accessible

### Encoding Task Stuck

**Symptom**: Tasks remain in queue indefinitely

**Solution**:

- Check if Celery worker is running: `celery -A src.main inspect active`
- Review Celery logs for errors
- Restart Celery worker: `celery -A src.main worker --loglevel=info`

### Runner Manager Unreachable

**Symptom**: `ConnectionError: Runner manager API error`

**Solution**:

- Verify `POD_ENCODING_MANAGER_URL` is correct
- Check network connectivity to Runner Manager
- Verify API token in `POD_ENCODING_MANAGER_TOKEN`

## Further Reading

- ⬅️ **[Back to Overview](README.md)**
- ⬅️ **[Back to Index](../README.md)**
