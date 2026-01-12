# CI/CD Documentation

This document describes the Continuous Integration (CI) and Continuous Deployment (CD) pipelines for the Pod project.
The pipelines are built using **GitHub Actions** and rely on **Docker** for environment consistency.

## Overview

The CI/CD process is divided into two main workflows:

1.  **Continuous Integration (`ci.yml`)**: Ensures code quality and correctness.
2.  **Dev Deployment (`build-dev.yml`)**: Builds and pushes the development Docker image.

## Workflows

### 1. Continuous Integration (`ci.yml`)

This workflow runs on every `push` and `pull_request`. It is designed to be **Cross-Platform** (Linux & Windows).

**Jobs:**

*   **`lint`**: Checks code style using `flake8` (runs on Ubuntu).
*   **`test-native`**: Validates the application in "Native" mode (without Docker).
    *   **Matrix Strategy**: Runs on both `ubuntu-latest` and `windows-latest`.
    *   **Steps**:
        1.  Installs dependencies (`pip install -r requirements.txt`).
        2.  Runs Unit Tests (`python manage.py test`).
        3.  **Smoke Test**: Starts the server (`runserver`) and checks health via `curl` to ensure the application boots correctly on the target OS.
*   **`test-docker`**: Validates the Docker build.
    *   **OS**: Runs on `ubuntu-latest` (Linux Containers).
    *   **Goal**: Ensures the Dockerfile builds correctly and tests pass inside the container.
*   **`test-docker-windows`**: Validates Docker commands on Windows.
    *   **OS**: Runs on `windows-latest`.
    *   **Goal**: Verifies that `docker build` and `docker run` commands work correctly in PowerShell, ensuring support for developers using Docker on Windows manually (without Makefile).

### 2. Dev Deployment (`build-dev.yml`)

This workflow runs on pushes to specific paths (source code, requirements, deployment config) to build the development image.

**Steps:**
1.  **Checkout**: Retries the code.
2.  **Metadata**: extracts tags and labels (e.g., branch name, commit SHA).
3.  **Build & Push**: Uses `docker/build-push-action` to build the image using `deployment/dev/Dockerfile` and push it to the GitHub Container Registry (GHCR).

## Local Development & verification

To verify your changes locally in an environment identical to the CI:

### Running Tests with Docker

You can reproduce the CI test step locally using Docker. This ensures that if it passes locally, it should pass in CI.

```bash
# 1. Build the test image (same as CI)
docker build -t test-ci-local -f deployment/dev/Dockerfile .

# 2. Run the tests
# Note: We pass dummy env vars as they are required for settings, but actual values don't matter for basic tests.
docker run --rm \
  -e SECRET_KEY=dummy \
  -e DJANGO_SETTINGS_MODULE=config.django.test.test \
  -e VERSION=TEST-LOCAL \
  test-ci-local \
  python manage.py test --settings=config.django.test.test
```

## Maintenance & Scalability

### Adding dependencies
If you add a Python dependency, update `requirements.txt`. The CI will automatically pick it up in the next run because the Docker image `COPY`s this file and installs requirements.

### Adding new checks
To add a new check (e.g., security scan, formatting check):
1.  Edit `.github/workflows/ci.yml`.
2.  Add a new job or step.
3.  **Recommendation**: If the tool requires specific dependencies, consider running it inside the Docker container (like the `test` job) or ensure `pip` caching is used if running on the runner directly.

### Troubleshooting
*   **"ImproperlyConfigured"**: Often due to missing environment variables. Check the `env:` section in the workflow or the `-e` flags in `docker run`.
*   **Cache issues**: If dependencies seem outdated in the `lint` job, the cache key (hash of requirements.txt) might be stale or the cache might need clearing via GitHub UI.
