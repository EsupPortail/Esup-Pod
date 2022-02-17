#!/bin/bash
# main
cd /usr/local/django_projects/podv2 && /home/pod/.virtualenvs/django_pod/bin/python manage.py index_videos --all &>> /usr/local/django_projects/podv2/pod/log/cron_index.log 2>&1