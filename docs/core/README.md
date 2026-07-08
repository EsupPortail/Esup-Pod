# Core & Management: Overview

The **Core** application provides essential management commands and utilities for maintaining project integrity and keeping documentation synchronized.

## Purpose

The Core app ensures that:

1. **Settings are audited** - All Django settings are documented and synchronized.
2. **Documentation is automated** - Configuration documentation is generated from a single source of truth.
3. **Data integrity is maintained** - Management commands help diagnose and fix common issues.

## Key Components

| Component               | Role                                                                      |
| :---------------------- | :------------------------------------------------------------------------ |
| **configuration.json**  | Single source of truth containing metadata for all configurable settings. |
| **Management Commands** | CLI tools for auditing, documenting, and maintaining the platform.        |

## Supported Commands

- **`comparesettings`**: Audit that all Python settings are documented in configuration.json.
- **`addsetting`**: Interactive CLI to add new settings properly to configuration.json.
- **`createconfiguration`**: Generate bilingual configuration documentation (FR/EN).

## Workflow

1. Developers define settings in Python.
2. `comparesettings` verifies they're documented.
3. `addsetting` helps add missing settings.
4. `createconfiguration` generates end-user documentation.

## Further Reading

- ➡️ **[Technical Details & Commands](details.md)**: Detailed usage of each management command.
- ⬅️ **[Back to Index](../README.md)**
