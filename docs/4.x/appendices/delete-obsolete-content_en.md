---
layout: default
version: 4.x
lang: en
---

# Deleting obsolete content in Pod

## Delete orphaned files

If your Esup-Pod server has been running for a long time, some files may be present on the disk but no longer correspond to existing videos in the database.

A script has been created to perform this task (command `clean_video_files`).

| Script                                             |
|----------------------------------------------------|
| pod/video/management/commands/clean_video_files.py |
{: .table .table-striped}

All you need to do is navigate to the correct environment:

```sh
cd /usr/local/django_projects/podv4/
workon django_pod4
```

When launched without parameters, it will scan all the video files on your server and automatically delete those that are not linked to a ‘video’ item:

```sh
python manage.py clean_video_files
```

The command accepts a `--type` argument that allows you to choose whether you want to delete videos (default value), user folders, or both (all).

Command examples:

```sh
python manage.py clean_video_files --type=userfolder --dry
python manage.py clean_video_files --type=all --dry
```

The `--dry` parameter allows you to run a simulation, just to see the list of what would be deleted without actually deleting anything.
Check the list of items to be deleted, then run the command again without the `-–dry` parameter to permanently delete them.

Use this cron command to clean these files regularly:

```sh
# Delete orphaned files
00 02 1 * * poduser cd /data/www/poduser/django_projects/podv4 && /data/www/poduser/.virtualenvs/django_pod4/bin/python manage.py clean_video_files
```

## Delete obsolete chunks

This cron command will cleanup the `chunked_upload` folder:

```sh
# Delete obsolete chunks
04 04 * * 0 poduser find /data/www/poduser/media/chunked_uploads -mtime +14 -delete &>> /var/log/pod/cron_clear_chunks.log 2>&1
```
