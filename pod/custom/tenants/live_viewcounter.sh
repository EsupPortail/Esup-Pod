#!/bin/bash
# Main
cd /usr/local/django_projects/podv2 && /home/pod/.virtualenvs/django_pod/bin/python manage.py live_viewcounter  >> /usr/local/django_projects/podv2/pod/log/cron_viewcounter.log 2>&1 
