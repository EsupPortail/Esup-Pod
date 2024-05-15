#!/bin/bash
## Variable à définir

NAME=$1

echo "remove previous tenant $NAME"
rm -rf "./$NAME"
sudo systemctl stop "uwsgi-pod_$NAME"
sudo rm -f "/etc/systemd/system/uwsgi-pod_$NAME.service"
sudo rm -f "/etc/nginx/sites-enabled/pod_nginx_$NAME.conf"
sudo rabbitmqctl delete_vhost "rabbitpod-$NAME"
