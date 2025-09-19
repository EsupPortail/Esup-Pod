---
layout: default
version: 4.x
lang: en
---

# Deleting obsolete content in Pod

If your Esup-Pod server has been running for a long time, some files may be present on the disk but no longer correspond to existing videos in the database.

A script has been created to perform this task (command `clean_video_files`).

| Script                                             |
|----------------------------------------------------|
| pod/video/management/commands/clean_video_files.py |
{: .table .table-striped}

All you need to do is navigate to the correct environment:

```bash
cd /usr/local/django_projects/podv4/
workon django_pod4
```

When launched without parameters, it will scan all the video files on your server and automatically delete those that are not linked to a ‘video’ item:

```bash
python manage.py clean_video_files
```

Starting with version 3.2 of Esup-Pod, the command accepts a `--type` argument that allows you to choose whether you want to delete videos (default value), user folders, or both (all).

Example commands:

```bash
python manage.py clean_video_files --type=userfolder --dry

python manage.py clean_video_files --type=all --dry
```

The `--dry` parameter allows you to run a simulation, just to see the list of what would be deleted without actually deleting anything.
Check the list of items to be deleted, then run the command again without the `-–dry` parameter to permanently delete them.
