# Configuration Guide

This guide describes how to configure **Esup-Pod**.
The project adheres to the [Twelve-Factor App](https://12factor.net/config) methodology, storing configuration in the **environment**.

## Configuration Hierarchy

1. **Environment Variables (`.env`)**: The source of truth.
2. **`src/config/env.py`**: Loads the `.env` file using the `django-environ` library.
3. **Django Settings (`src/config/django/`)**:
   - `base.py`: Core settings shared by all environments.
   - `dev/docker.py`: Development overrides (consumes `.env` defaults).
   - `test/docker.py`: Test-specific overrides (forces feature flags).

## 1. Configuration Hierarchy

The project follows a modular logic:

1. **Defaults**: Defined in `src/config/defaults/{app_name}.py`. **Never modify these files.**
2. **Infrastructure & Secrets (`.env`)**: Environment variables for services (DB, Host, Keys).
3. **Application Overrides (`src/config/settings/{app_name}.py`)**: This is where functional customization happens (e.g., `video.py`, `authentication.py`).

---

## 2. How to Customize My Instance?

To modify behavior (upload limits, colors, module activation):

1. **Identify the application** concerned in `docs/` (e.g., `docs/authentication/`).
2. **Create the override file** in `src/config/settings/` if it does not exist (e.g., `src/config/settings/video.py`).
   - You can take inspiration from the `.example` files present in this folder.

3. **Add your variables** in UPPERCASE. They will overwrite the default values when the application starts.

> [!TIP]
> To see the complete list of available variables for an application, consult the corresponding `src/config/defaults/{app_name}.py` file.
