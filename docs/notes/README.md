# Notes: Overview

The **Notes** application enables authenticated users to take personal or shared notes on videos. Notes can be attached to a specific timestamp or left as global comments on the video.

## Key Features

| Feature                | Description                                                                        |
| :--------------------- | :--------------------------------------------------------------------------------- |
| **Timestamped Notes**  | Attach a note to a specific moment in the video (in seconds).                      |
| **Global Notes**       | Leave a general note on a video without a specific timestamp.                      |
| **Privacy Control**    | Notes can be private (owner only) or public (visible to all video viewers).        |
| **Owner-only Edit**    | Only the author of a note can modify or delete it.                                 |
| **Filtered Listing**   | Notes are filtered by video and privacy — private notes are never exposed to others.|
| **Feature Flag**       | The entire notes system can be disabled via `USE_NOTES` configuration.             |

## Privacy Model

| Status      | Visibility                                          |
| :---------- | :-------------------------------------------------- |
| **Private** | Only visible to the note author.                    |
| **Public**  | Visible to all users who have access to the video.  |

## Data Models

| Model         | Role                                                                         |
| :------------ | :--------------------------------------------------------------------------- |
| **VideoNote** | A user note attached to a video, with optional timestamp and privacy status. |

## API Endpoints

| Method       | Endpoint              | Description                                                   |
| :----------- | :-------------------- | :------------------------------------------------------------ |
| **GET**      | `/api/notes/`         | List notes. Filter by `?video=<slug>`.                        |
| **POST**     | `/api/notes/`         | Create a new note (owner assigned automatically).             |
| **GET**      | `/api/notes/{id}/`    | Retrieve a single note.                                       |
| **PATCH**    | `/api/notes/{id}/`    | Update a note (owner only).                                   |
| **DELETE**   | `/api/notes/{id}/`    | Delete a note (owner only).                                   |

## Further Reading

- ➡️ **[Technical Details & Configuration](details.md)**: Model, permissions, serializer, and settings.
- ⬅️ **[Back to Index](../README.md)**