---
layout: default
version: 4.x
lang: en
---

# Regenerate thumbnails for videos

A script has been created to perform this task (`create_thumbnail` command).

| Script                                           |
|--------------------------------------------------|
| pod/video/management/commands/create_thubnail.py |
{: .table .table-striped}

All you need to do is position yourself in the right environment:

```bash
cd /usr/local/django_projects/podv4/
workon django_pod4
```

And run the regeneration command:

```bash
python manage.py create_thumbnail video_id1 video_id2
```

Remember to change the video IDs in the command.
{: .alert .alert-warning}
