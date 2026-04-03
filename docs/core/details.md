# Core & Management: Technical Details

This document details the maintenance tools developed for the **core** application of Pod V5. These commands ensure project integrity by linking the source code (Python), the data repository (JSON), and the user documentation (Markdown).
>
> **Navigation:** [Back to Overview](README.md) | [Back to Index](../README.md)

This document details the maintenance tools developed for the **core** application of Pod V5. These commands ensure project integrity by linking the source code (Python), the data repository (JSON), and the user documentation (Markdown).

---

## Overview

To keep technical documentation always up to date, Pod V5 uses a `configuration.json` file as the **single source of truth**. This file contains metadata for each setting:

- Supported versions

- Bilingual descriptions (FR/EN)

- Default values

The commands below automate the synchronization between this file and the rest of the system.

---

## 1. Compliance Audit: `comparesettings`

**Purpose:** Verify that all settings defined in the Python code are documented in the JSON repository.

### Internal Logic (comparesettings)

1. **Scan**: Analyzes active Django settings via `dir(settings)`.
2. **Filter**: Ignores internal and technical variables (via `IGNORED_PREFIXES`).
3. **Comparison**: Checks the results against the `configuration_pod` and `configuration_apps` sections of the JSON file.

### Usage (comparesettings)

```bash
python manage.py comparesettings

```

**Result:** Returns success if everything is synchronized, or an error listing missing settings with a non-zero exit code (ideal for CI).

---

## 2. Addition Assistant: `addsetting`

**Purpose:** Properly add a new setting to the JSON file without syntax errors.

### Internal Logic (addsetting)

- **Interactive Interface** asking for the target application (pod or business application).
- **Metadata Collection**: Start/end versions, default value, and FR/EN descriptions.
- **Secure Save** in `src/apps/core/configuration.json`.

### Usage (addsetting)

```bash
python manage.py addsetting <app_name> <setting_name>

```

---

## 3. Documentation Generator: `createconfiguration`

**Purpose:** Transform the technical JSON into readable Markdown files for end users.

### Internal Logic (createconfiguration)

- **Extraction**: Builds a structured document from the JSON.
- **Formatting**: Handles rich text formats and code blocks.
- **Internationalization**: Supports bilingual descriptions.

### Usage (createconfiguration)

```bash

# Generate documentation in French (CONFIGURATION_FR.md)
python manage.py createconfiguration fr
# Generate documentation in English (CONFIGURATION_EN.md)
python manage.py createconfiguration en

```

---

## CI/CD Integration

The `comparesettings` script is integrated into the **GitHub Actions** quality pipeline. It ensures that no new code can be merged if its settings are not documented.

```yaml

- name: Settings Audit
  run: python manage.py comparesettings
  env:
    VERSION: "5.0.0"
    SECRET_KEY: "ci-key"
    DJANGO_SETTINGS_MODULE: "config.django.base"

```

---
>
> **Pod V5 Team** | [Documentation Index](../README.md)

## Further Reading

- ⬅️ **[Back to Overview](README.md)**

- ⬅️ **[Back to Index](../README.md)**
