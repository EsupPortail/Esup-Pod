<!-- markdownlint-disable-file MD029 -->

# EsupPod V5 Release Process

This document describes the consensus procedure for publishing a new version of the **Pod_V5_Back** application to the GitHub Container Registry (GHCR).

## Release Workflow

To ensure stability and follow the project consensus, follow these steps in order:

1. **PR Acceptance**: Wait for your Pull Request from `origin/dev_v5` (your fork) to `upstream/dev_v5` (main repository) to be reviewed and merged.
2. **Local Sync**: Update your local `dev_v5` branch with the latest changes from the `upstream` repository.

```bash
   git fetch upstream
   git checkout dev_v5
   git merge upstream/dev_v5
```

3. **Tagging**: Once the code is merged, create a Git tag following the `vX.Y.Z` convention.

```bash
   git tag v5.0.0
```

4. **Pushing the Tag**: Push the tag to the `upstream` repository (or your fork if you have write access).

```bash
   git push upstream v5.0.0
```

## Automation

Adding a tag starting with `v` triggers the [Publish Docker Image to GHCR](.github/workflows/release.yml) GitHub Action automatically:

- It builds the Docker image using `deployment/dev/Dockerfile`.
- It publishes the image to `ghcr.io` with tags for the specific version and `latest`.

## Verification

You can monitor the progress in the **Actions** tab of the GitHub repository. Once completed, the image will be available in the **Packages** section.

---

_See also: [Contributing Guide](../CONTRIBUTING.md)_
