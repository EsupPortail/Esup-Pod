# Utils: Overview

The **Utils** application contains shared core utilities, abstract models, and helper functions used across various modules in the Esup-Pod V5 ecosystem.

## Key Features

| Feature                | Description                                                                                                         |
| :--------------------- | :------------------------------------------------------------------------------------------------------------------ |
| **Custom Image Model** | An abstract Django model handling responsive image uploads and automatic cropping.                                  |
| **File Storage Paths** | Centralized helper functions (`paths.py`) for generating dynamic upload directory paths (e.g., UUID-based hashing). |
| **File Deletion**      | Utilities (`files.py`) for securely deleting physical files from the storage server.                                |

## Data Models

| Model                | Role                                                                                                                                                                         |
| :------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CustomImageModel** | _Abstract Base Class._ Provides standardized fields (`file`, `width`, `height`, `x`, `y`) and Pillow-based cropping logic. Inherited by models like `Channel`, `Theme`, etc. |

## API Endpoints

_This application is strictly internal and does not expose any REST API endpoints._

## Further Reading

- ⬅️ **[Back to Index](../README.md)**
