# Maintenance & Management Commands

This document is the **reference guide for any developer maintaining a Pod V5 instance**. It covers all available `manage.py` commands organized by functional domain.

This document details the maintenance tools developed for the **core** application of Pod V5. These commands ensure project integrity by linking the source code (Python), the data repository (JSON), and the user documentation (Markdown).
> **Navigation:** [Back to Overview](README.md) | [Back to Index](../README.md)

---

## Quick Reference

| Domain            | Command                | When to run                                      |
| :---------------- | :--------------------- | :----------------------------------------------- |
| **Search**        | `reindex_videos`       | After deployment, data migration, or index corruption |
| **Cache**         | `warm_cache`           | After deployment or cache flush                  |
| **Migration**     | `import_data_from_v4_to_v5` | One-time V4 → V5 data migration           |
| **Config**        | `comparesettings`      | After adding new settings (CI/CD)                |
| **Config**        | `addsetting`           | Adding a new documented setting                  |
| **Config**        | `createconfiguration`  | Regenerating `CONFIGURATION.md`                  |
| **Config**        | `validate_config`      | Validating Pydantic settings at startup          |
| **Auth**          | `ensure_superuser`     | Creating the first admin user (Docker init)      |

---

## 1. Search — `reindex_videos`

**Purpose:** Build or rebuild the Redis Search full-text index from the database.
Run this after a fresh deployment, a data migration, or whenever the index becomes corrupted.

**Source:** [`src/apps/search/management/commands/reindex_videos.py`](../../src/apps/search/management/commands/reindex_videos.py)

### Usage

```bash
# Index all published videos (incremental — does not drop the index)
python manage.py reindex_videos

# Drop the existing index then rebuild from scratch (clean reindex)
python manage.py reindex_videos --drop

# Custom batch size (default: 100)
python manage.py reindex_videos --batch-size 200

# Combine: clean reindex with large batches
python manage.py reindex_videos --drop --batch-size 500
```

### When to run

| Situation                                   | Command                                    |
| :------------------------------------------ | :----------------------------------------- |
| First deployment                            | `reindex_videos --drop`                    |
| After `import_data_from_v4_to_v5`           | `reindex_videos --drop`                    |
| After bulk import via SQL / fixtures        | `reindex_videos`                           |
| Redis Search index corrupted / missing      | `reindex_videos --drop`                    |
| Adding a new indexed field                  | `reindex_videos --drop`                    |

> [!WARNING]
> `--drop` deletes the index before recreating it. During the reindex, search returns **no results**. Schedule this during off-peak hours in production.

---

## 2. Cache — `warm_cache`

**Purpose:** Pre-load the Redis cache (DB 1) with static data, and clear stale search cache entries.
Equivalent of V4's `cache_video_data` management command.

**Source:** [`src/apps/search/management/commands/warm_cache.py`](../../src/apps/search/management/commands/warm_cache.py)

### What it caches

| Cache key              | Content                                | TTL    |
| :--------------------- | :------------------------------------- | :----- |
| `pod:video:metadata`   | Licenses, cursus, languages, statuses  | 600s   |
| *(clears)*             | `pod:search:*` (all search results)    | —      |

### Usage

```bash
# Clear stale caches + preload static metadata
python manage.py warm_cache

# Clear only (no preloading) — useful after a bulk data change
python manage.py warm_cache --clear-only
```

### Recommended cron (production)

```cron
# Pre-warm cache every 10 minutes (keeps metadata fresh between invalidations)
*/10 * * * * cd /app && python manage.py warm_cache >> /var/log/pod/warm_cache.log 2>&1
```

### How cache invalidation works automatically

In normal operation, caches are invalidated **automatically** via Django signals — you don't need to run `warm_cache` manually after each video change:

```text
Video.save() / Video.delete()
        │
        ▼
signals.py → _invalidate_video_caches()
        ├── cache.delete_many(["pod:video:metadata"])
        └── cache.delete_pattern("pod:search:*")
```

Use `warm_cache` proactively after deployments or bulk operations to avoid a cold cache after restart.

> [!TIP]
> If `REDIS_CACHE_URL` is not set (local dev without Docker), `warm_cache` still runs but uses `LocMemCache`. The `delete_pattern` call is silently ignored.

---

## 3. Migration — `import_data_from_v4_to_v5`

**Purpose:** One-time import of V4 data (users, videos, channels, etc.) into the V5 database.

**Source:** [`src/apps/core/management/commands/import_data_from_v4_to_v5.py`](../../src/apps/core/management/commands/import_data_from_v4_to_v5.py)

### Usage

```bash
python manage.py import_data_from_v4_to_v5
```

> [!IMPORTANT]
> Run this command only **once** during migration. After import, always run `reindex_videos --drop` to rebuild the search index.

See also: [V4 → V5 Migration Guide](../deployment/migration_v4_to_v5_fr.md)

---

## 4. Config — `comparesettings`

**Purpose:** Audit that all Python settings are documented in `configuration.json`. Exits non-zero if any setting is missing (CI/CD integration).

**Source:** [`src/apps/core/management/commands/comparesettings.py`](../../src/apps/core/management/commands/comparesettings.py)

### Usage

```bash
python manage.py comparesettings
```

**Result:** `System OK` if everything is in sync, or a list of missing settings with a non-zero exit code.

### CI/CD integration

```yaml
- name: Settings Audit
  run: python manage.py comparesettings
  env:
    SECRET_KEY: "ci-key"
    DJANGO_SETTINGS_MODULE: "config.django.base"
```

---

## 5. Config — `addsetting`

**Purpose:** Interactively add a new setting to `configuration.json` with its metadata (versions, FR/EN descriptions, default value).

**Source:** [`src/apps/core/management/commands/addsetting.py`](../../src/apps/core/management/commands/addsetting.py)

### Usage

```bash
python manage.py addsetting <app_name> <SETTING_NAME>

# Example: document a new search setting
python manage.py addsetting search SEARCH_CACHE_TTL
```

---

## 6. Config — `createconfiguration`

**Purpose:** Regenerate `CONFIGURATION.md` (and its bilingual variants) from `configuration.json`.

**Source:** [`src/apps/core/management/commands/createconfiguration.py`](../../src/apps/core/management/commands/createconfiguration.py)

### Usage

```bash
python manage.py createconfiguration fr   # → CONFIGURATION_FR.md
python manage.py createconfiguration en   # → CONFIGURATION_EN.md
```

Run this after any `addsetting` call to keep end-user documentation in sync.

---

## 7. Config — `validate_config`

**Purpose:** Validate Pydantic settings at startup. Surfaces type errors and missing required values before the app starts serving requests.

**Source:** [`src/apps/core/management/commands/validate_config.py`](../../src/apps/core/management/commands/validate_config.py)

### Usage

```bash
python manage.py validate_config
```

---

## 8. Auth — `ensure_superuser`

**Purpose:** Create the first superuser from environment variables. Used in Docker entrypoints to bootstrap a fresh deployment.

**Source:** [`src/apps/core/management/commands/ensure_superuser.py`](../../src/apps/core/management/commands/ensure_superuser.py)

### Usage

```bash
python manage.py ensure_superuser
# Reads: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD
```

---

## Typical Maintenance Playbooks

### 🚀 Fresh deployment

```bash
python manage.py migrate
python manage.py ensure_superuser
python manage.py reindex_videos --drop
python manage.py warm_cache
```

### 🔄 After a bulk data import (SQL / fixtures)

```bash
python manage.py reindex_videos
python manage.py warm_cache --clear-only
```

### 🩹 Search is returning stale or no results

```bash
# 1. Drop and rebuild the Redis Search index
python manage.py reindex_videos --drop

# 2. Clear the Django search cache
python manage.py warm_cache --clear-only
```

### 🧹 Cache is stale after a deployment

```bash
python manage.py warm_cache
```

### 📝 After adding a new Django setting

```bash
python manage.py addsetting <app> <SETTING_NAME>
python manage.py createconfiguration fr
python manage.py createconfiguration en
python manage.py comparesettings  # Must return 0
```

---

## Further Reading

- ⬅️ **[Back to Overview](README.md)**
- ⬅️ **[Back to Index](../README.md)**
- ➡️ **[Search Technical Details](../search/details.md)**
- ➡️ **[Deployment & Redis Architecture](../deployment/README.md)**

