#!/bin/bash
# main
cd /usr/local/django_projects/podv2 && /home/pod/.virtualenvs/django_pod/bin/python manage.py clearsessions &>> /usr/local/django_projects/podv2/pod/log/cron_clearsessions.log 2>&1