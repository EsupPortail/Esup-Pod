# CI/CD Documentation

This document describes the Continuous Integration (CI) and Continuous Deployment (CD) pipelines for the Pod project.
The pipelines are built using **GitHub Actions** and rely on **Docker** for environment consistency.

## Overview

The CI/CD process is divided into two main workflows:

1.  **Continuous Integration (`ci.yml`)**: Ensures code quality and correctness.
2.  **Dev Deployment (`build-dev.yml`)**: Builds and pushes the development Docker image.


## Running Tests with Docker
To verify your changes locally in an environment identical to the CI

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

