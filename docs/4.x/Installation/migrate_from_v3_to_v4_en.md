
---
layout: default
version: 4.x
lang: en
---

- [Data migration system from Version 3 to Version 4](#data-migration-system-from-version-3-to-version-4)
  - [Prerequisites](#prerequisites)
  - [Exporting data from Pod v3](#exporting-data-from-pod-v3)
    - [Description](#description)
    - [Key features](#key-features)
    - [Important notes](#important-notes)
    - [Usage](#usage)
  - [Importing data into Pod v4](#importing-data-into-pod-v4)
    - [Description](#description-1)
    - [Key features](#key-features-1)
    - [Important notes](#important-notes-1)
    - [Usage](#usage-1)
      - [Arguments](#arguments)
      - [Examples](#examples)

# Data migration system from Version 3 to Version 4

This document describes the data migration process for the Pod application from version 3.8.x to version 4.0.x.
The system is based on two main scripts:
- one to export data from Pod v3 to a JSON file,
- the other to import that JSON file into Pod v4.

## Prerequisites

- A version of Pod in 3.8.x (3.8.1, 3.8.2, 3.8.3 and 3.8.4 at this time)
- A version of Pod in 4.0.x (currently 4.0.alpha)
- Make sure you have access to the Pod 3.8.x database (MariaDB/MySQL or PostgreSQL).
- Make sure you have access to the Pod 4.0.x database (MariaDB/MySQL or PostgreSQL).

---

## Exporting data from Pod v3

### Description

This first script exports data from the Pod v3.8.x database into a JSON file. It supports both MariaDB/MySQL and PostgreSQL and adapts SQL queries accordingly.

Note: This script must be run from a Pod v3 server.

The latest version of this script `export_data_from_v3_to_v4.py` is available here: [https://github.com/EsupPortail/Esup-Pod/tree/main/pod/video/management/commands](https://github.com/EsupPortail/Esup-Pod/tree/main/pod/video/management/commands)

You need to retrieve this script and place it in the `pod/video/management/commands` directory with the correct permissions.
{: .alert .alert-warning}

### Key features

- Exports specified tables from the Pod v3 database to a JSON file.
- Supports both MariaDB/MySQL and PostgreSQL.
- Creates a directory to store exported data if it does not already exist.
- Provides detailed success and error messages.

### Important notes

- The JSON file will be generated at this location: `BASE_DIR/data_from_v3_to_v4/v3_exported_tables.json`.
  - Example: `/usr/local/django_projects/data_from_v3_to_v4/v3_exported_tables.json`.

Check your `custom/settings_local.py` to find the configured `BASE_DIR` directory.
{: .alert .alert-warning}

- This script can be run as many times as needed; the JSON file is regenerated with each execution.

### Usage

Run the script from a Pod v3 server using the following command:

```bash
python manage.py export_data_from_v3_to_v4
```

---

## Importing data into Pod v4

### Description

This script imports data from the previously generated JSON file into a Pod v4 database. It supports MariaDB/MySQL and PostgreSQL, reads data from the specified JSON file, processes it, and inserts it into the appropriate tables in the Pod v4 database.

### Key features

- Imports a JSON file generated with specified tables from the Pod v3 database.
- Supports MariaDB/MySQL and PostgreSQL.
- Creates a directory to store exported data if it does not already exist (usually unnecessary).
- Provides detailed success and error messages.
- Supports tags management for videos and recorders via the Tagulous library.
- Can run a Bash command to create the database and initialize data.
- Supports secure error handling and a dry-run mode.

### Important notes

- The JSON file must be located at `BASE_DIR/data_from_v3_to_v4/v3_exported_tables.json`.
  - Example: `/usr/local/django_projects/data_from_v3_to_v4/v3_exported_tables.json`.

Check your `custom/settings_local.py` to find the configured `BASE_DIR` directory.
{: .alert .alert-warning}

- Set `DEBUG = False` in `settings_local.py` to avoid debug/warning/info messages.

- Can be used with MariaDB/MySQL or PostgreSQL databases.

- If you encounter a "Too many connections" error, you can increase the `time_sleep` variable.
  The process will take longer but will complete without error.

- This script can be run multiple times; data is deleted before re-insertion.

- Depending on your data, this script may take a long time to complete. Typically, importing the `video_viewcount` table is slow.
  Additionally, since the tags management library has changed between v3 and v4, specific processing is required and takes time to avoid "Too many connections" errors.

- After import, do not forget to make the Pod v3 `MEDIA_ROOT` accessible to Pod v4 servers.

- After import, do not forget to **re-index all videos** for Elasticsearch with:

```bash
python manage.py index_videos --all
```

### Usage

Run the script using the management command:

```bash
python manage.py import_data_from_v3_to_v4
```

#### Arguments

- `--dry`: Simulates what will be done (default=False).
- `--createDB`: Runs Bash commands to create tables in the database and add initial data (see `make createDB`). The database must be empty (default=False).
- `--onlytags`: Processes only the tags (default=False). Useful if you encounter the 'Too many connections' error when processing tags.

#### Examples

Dry run:
```bash
python manage.py import_data_from_v3_to_v4 --dry
```

If the database is completely empty (no tables), you can run this command which will perform a `make createDB` before importing data:
```bash
python manage.py import_data_from_v3_to_v4 --createDB
```

If you encountered a "Too many connections" error while importing tags, feel free to increase the `time_sleep` value (e.g., 0.4 or 0.5 seconds) and re-run the process, but only for tags:
```bash
python manage.py import_data_from_v3_to_v4 --onlytags
```

Of course, it is possible to mix the different arguments.

---

By following these instructions, you should be able to successfully migrate your Pod 3.8.x database to Pod 4.0.x.
