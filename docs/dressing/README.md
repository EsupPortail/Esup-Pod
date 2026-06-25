# Dressing: Overview

The **Dressing** application extends the Esup-Pod video ecosystem by providing automated video branding capabilities, such as adding watermarks (logos) and attaching intro/outro clips to videos.

## Key Features

| Feature                 | Description                                                                            |
| :---------------------- | :------------------------------------------------------------------------------------- |
| **Watermarks**          | Upload logos (images) to be overlaid on videos at specific positions (corners).        |
| **Generics**            | Upload short video clips to be used as intros or outros for main videos.               |
| **Dressing Assignment** | Attach a specific watermark and/or generic to a video.                                 |
| **Auto-reencoding**     | Automatically triggers an encoding task when a video's dressing configuration changes. |

## Data Models

| Model         | Role                                                                               |
| :------------ | :--------------------------------------------------------------------------------- |
| **Watermark** | Represents an image logo with a default transparency level.                        |
| **Generic**   | Represents a short video clip (intro/outro).                                       |
| **Dressing**  | The configuration linking a Video to a Watermark (with position) and/or a Generic. |

## API Endpoints

| Method        | Endpoint               | Description                                       |
| :------------ | :--------------------- | :------------------------------------------------ |
| **GET**       | `/api/watermarks/`     | List available watermarks.                        |
| **POST**      | `/api/watermarks/`     | Upload a new watermark image.                     |
| **GET**       | `/api/generics/`       | List available generic videos.                    |
| **POST**      | `/api/generics/`       | Upload a new generic video clip.                  |
| **GET**       | `/api/dressings/`      | List dressing configurations.                     |
| **POST**      | `/api/dressings/`      | Assign a dressing (watermark/generic) to a video. |
| **PATCH/DEL** | `/api/dressings/{id}/` | Modify or remove a video's dressing.              |

## Further Reading

- ⬅️ **[Back to Index](../README.md)**
