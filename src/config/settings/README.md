# Local Configuration Overrides

This directory is used for local configuration overrides.
Files in this directory are NOT tracked by git (except this README and example files).

## How to Customize

To customize your instance configuration (feature flags, limits, etc.):

1.  **Identify the app** you want to configure (e.g., `video`, `authentication`, `core`).
2.  **Create a new file** in this directory named `{app_name}.py` (e.g., `video.py`).
    *   You can copy one of the `.example` files if available (e.g., `cp video.py.example video.py`).
3.  **Add your overrides** to that file.

## Configuration Loading Order

The application loads settings in the following order:

1.  **Defaults**: `src/config/defaults/{app_name}.py` (Project defaults)
2.  **Overrides**: `src/config/settings/{app_name}.py` (Your local overrides)

Only variables in **UPPERCASE** are loaded into Django settings.

## Example

To change the video upload size limit:

1.  Create `src/config/settings/video.py`
2.  Add:
    ```python
    MAX_UPLOAD_SIZE_GB = 10
    ```
