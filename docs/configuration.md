# Configuration Guide

This guide describes how to configure **Esup-Pod V5**.
The project adheres to the [Twelve-Factor App](https://12factor.net/config) methodology, storing configuration in the **environment**.

## Configuration Hierarchy

1.  **Environment Variables (`.env`)**: The source of truth.
2.  **`src/config/env.py`**: Loads the `.env` file using the `django-environ` library.
3.  **Django Settings (`src/config/django/`)**:
    *   `base.py`: Core settings shared by all environments.
    *   `dev/docker.py`: Development overrides (consumes `.env` defaults).
    *   `test/docker.py`: Test-specific overrides (forces feature flags).

---

## 2. Environment Variables Reference

Create a `.env` file in the project root to set these variables.

### Core Settings

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| **`DJANGO_SETTINGS_MODULE`** | ✅ | `config.django.base` | Python path to settings module. (e.g. `config.django.dev.docker`) |
| **`SECRET_KEY`** | ✅ | *(None)* | Django security key. **Must be secret in production.** |
| **`VERSION`** | ❌ | `5.0.0-DEV` | Application version tag. |
| **`EXPOSITION_PORT`** | ❌ | `8000` | Port exposed by Docker to the host. |

### Database (MySQL/MariaDB)

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| **`MYSQL_DATABASE`** | ❌ | `pod_db` | Database name. |
| **`MYSQL_USER`** | ❌ | `pod` | Database user. |
| **`MYSQL_PASSWORD`** | ❌ | `pod` | Database password. |
| **`MYSQL_ROOT_PASSWORD`** | ❌ | *(None)* | Root password for DB container initialization. |
| **`MYSQL_HOST`** | ❌ | `db` | Hostname of the DB service (Docker service name). |
| **`MYSQL_PORT`** | ❌ | `3306` | Port of the DB service. |

### Authentication Feature Flags

Modules can be enabled/disabled without changing code.

| Variable | Default | Description |
| :--- | :--- | :--- |
| **`USE_LOCAL_AUTH`** | `True` | Enable standard Django Database authentication. |
| **`USE_LDAP`** | `False` | Enable LDAP authentication backend. |
| **`USE_CAS`** | `False` | Enable CAS authentication backend. |
| **`USE_SHIB`** | `False` | Enable Shibboleth authentication. |
| **`USE_OIDC`** | `False` | Enable OpenID Connect authentication. |

### LDAP Configuration (If enabled)

| Variable | Description |
| :--- | :--- |
| **`AUTH_LDAP_BIND_PASSWORD`** | Password for the Bind DN user. |

*(Note: Other LDAP settings like Server URL are currently hardcoded in `src/config/settings/authentication.py` but will be moved to env vars in future updates.)*

---

## 3. How to Customize Settings

### Adding a new setting
1.  Define the variable in your `.env` file.
2.  Read it in the appropriate settings file using `env()`:

    ```python
    from config.env import env

    MY_CUSTOM_SETTING = env("MY_CUSTOM_SETTING", default="default_value")
    ```

### Overriding for Local Development
Do **not** create a `settings_local.py`. Instead:
1.  Add the override to your `.env` file.
2.  Restart the container (`make start`).

### Adding a new App
1.  Create the app in `src/apps/`.
2.  Add it to `INSTALLED_APPS` in `src/config/django/base.py`.
