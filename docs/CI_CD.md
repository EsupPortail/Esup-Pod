# CI/CD Documentation

This document describes the Continuous Integration (CI) and Continuous Deployment (CD) pipelines for the Pod project.
The pipelines are built using **GitHub Actions** and rely on **Docker** for environment consistency.

## Overview

The CI/CD process is divided into two main workflows:

### Workflows

#### 1. Continuous Integration (`ci.yml`)

This workflow runs on every `push` and `pull_request`.

**Jobs:**
*   **`quality-check`**: Checks code style using `flake8`.
*   **`check-schema`**: **[NEW]** Verifies that `docs/api-docs.yaml` matches the codebase. Fails if out of sync.
*   **`test-native`**: Validates the application on the runner (Ubuntu & Windows).
*   **`test-docker-full`**: Starts the full stack (App + MySQL + Redis) in Docker and runs tests.
    *   **Coverage Enforced**: The job fails if test coverage is below **70%**.

## Running Tests Locally

To reproduce the CI environment exactly:

### Using Docker (Recommended)
You can run the full test suite inside the Docker container, exactly as the CI does:

```bash
# 1. Start the stack
docker compose -f deployment/ci/docker-compose.test.yml up -d

# 2. Run tests (e.g., matching the CI command)
docker compose -f deployment/ci/docker-compose.test.yml exec api pytest --cov=src --cov-report=term-missing --cov-fail-under=70

# 3. Teardown
docker compose -f deployment/ci/docker-compose.test.yml down -v
```

