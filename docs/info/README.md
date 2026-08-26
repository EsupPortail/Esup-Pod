# Info: Overview

The **Info** application provides read-only endpoints that expose public configuration and system versioning details. It allows the frontend to adapt dynamically to the backend's capabilities without exposing any sensitive infrastructure details.

## Key Features

| Feature                   | Description                                                                      |
| :------------------------ | :------------------------------------------------------------------------------- |
| **System Info**           | Exposes the project name and current version (e.g., POD V5 - 5.0.0).             |
| **Dynamic Configuration** | Exposes whitelisted (public) feature flags and limits from the backend settings. |

## Data Models

_This application does not manage any database models. It relies directly on `django.conf.settings` and Pydantic configuration schemas._

## API Endpoints

| Method  | Endpoint            | Description                                    |
| :------ | :------------------ | :--------------------------------------------- |
| **GET** | `/api/info/`        | Retrieve project name and version.             |
| **GET** | `/api/info/config/` | Retrieve all public application feature flags. |

## Further Reading

- ⬅️ **[Back to Index](../README.md)**
