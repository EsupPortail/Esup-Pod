# Pod V5 Documentation

Welcome to the Pod V5 Project Documentation. This guide is intended for developers, administrators, and contributors.

## Table of Contents

### [Authentication](authentication/README.md)
Understand and configure security.
*   [Overview](authentication/README.md): Supported methods (Local, CAS, LDAP).
*   [Technical Details](authentication/details.md): Advanced configuration, attribute mapping, and internal workings.

### [API & Swagger](api/README.md)
Interact with the backend via the REST API.
*   [Swagger Access](api/README.md): Links to interactive documentation.
*   [Developer Guide](api/guide.md): How to document new endpoints.

### [Deployment & CI/CD](deployment/README.md)
Architecture, production setup, and automation.
*   [Deployment Overview](deployment/README.md): System architecture.
*   [Development Guide](deployment/dev/dev.md): How to setup local environment (Docker/Make).
*   [CI/CD Pipelines](CI_CD.md): Understanding the GitHub Actions workflows.

### [AI & LLM Helpers](LLM_HELPERS.md)
Tools and configurations for AI agents.
*   [Overview](LLM_HELPERS.md): `llms.txt` documentation context.

### [Configuration](configuration.md)
*   [Environment Variables](configuration.md): Complete list of .env variables.
*   [Customization](configuration.md#3-how-to-customize-settings): How to add settings or apps.

## Project Structure

```bash
Pod_V5/
├── src/
│   ├── apps/           # Django Apps (Business Logic)
│   └── config/         # Configuration & Settings
│       ├── django/     # Django Settings (Base, Dev, Test, Prod)
│       └── settings/   # Feature-specific settings (Auth, API, etc.)
├── deployment/         # Docker Configuration
├── docs/               # Documentation (You are here)
└── manage.py           # Django CLI
```

## Configuration Hierarchy

The project uses a **Environment Variable Driven** configuration:

1.  **Docker / System**: Environment variables are set in `.env` (or CI secrets).
2.  **`src/config/env.py`**: Loads variables using `django-environ`.
3.  **`src/config/django/*.py`**: Settings files consume these variables.
    *   **Features Flags**: `USE_LDAP`, `USE_CAS`, etc. are toggled via env vars.
    *   **No `settings_local.py`**: We do not use local python override files. Use `.env` for everything.
