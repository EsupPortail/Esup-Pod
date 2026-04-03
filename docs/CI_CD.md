# CI/CD & Testing: Overview

This document describes the Continuous Integration (CI) and Continuous Deployment (CD) pipelines for the Pod project.
The pipelines are built using GitHub Actions and rely on Docker for environment consistency.

## Overview

The CI/CD process is streamlined to use a Single Source of Truth: the Docker environment. Our local Makefile mirrors the logic used in GitHub Actions.

### Workflows

#### 1. Continuous Integration (`ci.yml`)

This workflow runs on every `push` and `pull_request`.

**Jobs:**

- **`quality-check`**: Checks code style using `flake8` and formatting with `black`.
- **`test-docker-full`**: Equivalent to make test-cov.
  - Builds the stack.
  - Runs the full Python test suite.
  - Coverage Enforced: The job fails if test coverage is below than is descided.

## Running Pipelines Locally

You can run the exact same sequence as the CI on your machine to ensure your PR will pass:

```shell
make ci
```

This command chains: build ➔ lint ➔ test-cov ➔ clean.

## Running Tests Locally

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

- **Database**: Uses a separate `test_pod_db` MySQL database.
- **Settings**: Uses `src/config/django/test/docker.py`.

## Further Reading

- ⬅️ **[Back to Index](README.md)**
