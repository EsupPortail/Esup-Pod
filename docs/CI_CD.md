# CI/CD Documentation

This document describes the Continuous Integration (CI) and Continuous Deployment (CD) pipelines for the Pod project.
The pipelines are built using **GitHub Actions** and rely on **Docker** for environment consistency.

## Overview

The CI/CD process is streamlined to use a **Single Source of Truth**: the Docker environment.

### Workflows

#### 1. Continuous Integration (`ci.yml`)

This workflow runs on every `push` and `pull_request`.

**Jobs:**
*   **`quality-check`**: Checks code style using `flake8`.
*   **`test-docker-full`**: The authoritative test suite.
    *   Builds the stack using `deployment/dev/docker-compose.yml`.
    *   Validates the OpenAPI schema consistency (inside Docker).
    *   Runs the full Python test suite with `pytest` (inside Docker).
    *   Runs E2E scenarios against the running API.
    *   **Coverage Enforced**: The job fails if test coverage is below **60%**.

## Running Tests Locally

To reproduce the CI environment exactly:

### Using Make (Recommended)

Simply run:

```bash
make test
```

This will run `pytest` inside the running Docker container, using the dedicated test settings (`config.django.test.docker`).

### Manual Docker Command

If you do not have `make` or want to run the raw command:

```bash
docker compose -f deployment/dev/docker-compose.yml exec -e DJANGO_SETTINGS_MODULE=config.django.test.docker api pytest --cov=src
```

### Test Environment Details

*   **Database**: Uses a separate `test_pod_db` MySQL database.
*   **Authentication**: explicitely enables `USE_LDAP`, `USE_CAS`, `USE_SHIB`, `USE_OIDC` to verify auth flows.
*   **Settings**: Uses `src/config/django/test/docker.py`.
