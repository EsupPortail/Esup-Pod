#!/bin/bash

# Main
cd /usr/local/django_projects/podv2 && /home/pod/.virtualenvs/django_pod/bin/python manage.py check_obsolete_videos >> /usr/local/django_projects/podv2/pod/log/cron_obsolete.log 2>&1