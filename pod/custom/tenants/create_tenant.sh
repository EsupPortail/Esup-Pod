#!/bin/bash
## Variable à définir
NAME=$2
ID_SITE=$1
DOMAIN_NAME=$3

echo "Script executed from: ${PWD}"

BASEDIR=${PWD}

echo "remove previous site"
rm -rf "./$NAME"
sudo systemctl stop uwsgi-pod_$NAME
sudo rm -f "/etc/systemd/system/uwsgi-pod_$NAME.service"
sudo rm -f "/etc/nginx/sites-enabled/pod_nginx_$NAME.conf"
sudo rabbitmqctl delete_vhost rabbitpod-$NAME


echo "Creation du site numéro $ID_SITE ayant pour identifiant $NAME et pour domaine $DOMAIN_NAME"
echo "Creation du répertoire"
cp -r ./source "./$NAME"

echo "Fichier de configuration"
mv "./$NAME/tenant_settings.py" ./$NAME/"$NAME"_settings.py
sed -i "s/__NAME__/$NAME/g" ./$NAME/"$NAME"_settings.py
sed -i "s/__ID_SITE__/$ID_SITE/g" ./$NAME/"$NAME"_settings.py
sed -i "s/__DOMAIN_NAME__/$DOMAIN_NAME/g" ./$NAME/"$NAME"_settings.py

echo "Fichier vhost nginx"
mv "./$NAME/pod_nginx_tenant.conf" "./$NAME/pod_nginx_$NAME.conf"
sed -i "s/__NAME__/$NAME/g" "./$NAME/pod_nginx_$NAME.conf"
sed -i "s/__ID_SITE__/$ID_SITE/g" "./$NAME/pod_nginx_$NAME.conf"
sed -i "s/__DOMAIN_NAME__/$DOMAIN_NAME/g" "./$NAME/pod_nginx_$NAME.conf"

echo "Fichier ini"
mv "./$NAME/pod_uwsgi_tenant.ini" "./$NAME/pod_uwsgi_$NAME.ini"
sed -i "s/__NAME__/$NAME/g" "./$NAME/pod_uwsgi_$NAME.ini"
sed -i "s/__ID_SITE__/$ID_SITE/g" "./$NAME/pod_uwsgi_$NAME.ini"
sed -i "s/__DOMAIN_NAME__/$DOMAIN_NAME/g" "./$NAME/pod_uwsgi_$NAME.ini"

echo "Activation du vhost"
sudo ln -s "$BASEDIR/$NAME/pod_nginx_$NAME.conf" "/etc/nginx/sites-enabled/pod_nginx_$NAME.conf"
## sudo /etc/init.d/nginx restart
echo "****************"
echo "--> add /home/pod/ssl/$NAME/$DOMAIN_NAME.crt and add /home/pod/ssl/$NAME/$DOMAIN_NAME.key"
echo "--> then restart nginx with sudo /etc/init.d/nginx restart"
echo "****************"

echo "Activation du service uwsgi"
mv "./$NAME/uwsgi-pod_tenant.service" "./$NAME/uwsgi-pod_$NAME.service"
sed -i "s/__NAME__/$NAME/g" "./$NAME/uwsgi-pod_$NAME.service"
sudo ln -s "$BASEDIR/$NAME/uwsgi-pod_$NAME.service" "/etc/systemd/system/uwsgi-pod_$NAME.service"
sudo systemctl enable uwsgi-pod_$NAME
echo "****************"
echo "--> after restarting nginx, use $> sudo systemctl start uwsgi-pod_$NAME"
echo "--> to start the site"
echo "****************"

echo "Add vhost to rabbitmq"
sudo rabbitmqctl add_vhost rabbitpod-$NAME
sudo rabbitmqctl set_permissions -p rabbitpod-$NAME pod ".*" ".*" ".*"

echo "Données initiales"
sed -i "s/__NAME__/$NAME/g" "./$NAME/initial_data.json"
sed -i "s/__ID_SITE__/$ID_SITE/g" "./$NAME/initial_data.json"
sed -i "s/__DOMAIN_NAME__/$DOMAIN_NAME/g" "./$NAME/initial_data.json"
echo "--"
echo "Pour intégrer les données en base concernant ce nouveau site, il faut lancer la commande suivante:"
echo "(django_pod) pod@pod:/usr/local/django_projects/podv3$ python manage.py loaddata pod/custom/tenants/$NAME/initial_data.json --settings=pod.custom.tenants.$NAME.\"$NAME\"_settings"
echo "--"
echo "N'oubliez pas de créer l'index dans elasticseach via cette commande :"
echo "(django_pod) pod@pod:/usr/local/django_projects/podv3$ python manage.py create_pod_index --settings=pod.custom.tenants.$NAME."$NAME"_settings"
echo "--"
echo "crontab"
echo "clear session"
echo "" >> "$BASEDIR/sh_tenants/clearsessions.sh"
echo "# $ID_SITE $NAME " >> "$BASEDIR/sh_tenants/clearsessions.sh"
echo "cd /usr/local/django_projects/podv3 && /home/pod/.virtualenvs/django_pod/bin/python manage.py clearsessions --settings=pod.custom.tenants.$NAME.\"$NAME\"_settings &>> /usr/local/django_projects/podv3/pod/log/cron_clearsessions_$NAME.log 2>&1" >> "$BASEDIR/clearsessions.sh"

echo "index videos"
echo "" >> "$BASEDIR/sh_tenants/index_videos.sh"
echo "# $ID_SITE $NAME " >> "$BASEDIR/sh_tenants/index_videos.sh"
echo "cd /usr/local/django_projects/podv3 && /home/pod/.virtualenvs/django_pod/bin/python manage.py index_videos --all  --settings=pod.custom.tenants.$NAME.\"$NAME\"_settings  &>> /usr/local/django_projects/podv3/pod/log/cron_index_$NAME.log 2>&1"  >> "$BASEDIR/index_videos.sh"

echo "check_obsolete_videos"
echo "" >> "$BASEDIR/sh_tenants/check_obsolete_videos.sh"
echo "# $ID_SITE $NAME " >> "$BASEDIR/sh_tenants/check_obsolete_videos.sh"
echo "cd /usr/local/django_projects/podv3 && /home/pod/.virtualenvs/django_pod/bin/python manage.py check_obsolete_videos --settings=pod.custom.tenants.$NAME.\"$NAME\"_settings  &>> /usr/local/django_projects/podv3/pod/log/cron_obsolete_$NAME.log 2>&1"  >> "$BASEDIR/check_obsolete_videos.sh"

echo "live_viewcounter"
echo "" >> "$BASEDIR/sh_tenants/live_viewcounter.sh"
echo "# $ID_SITE $NAME " >> "$BASEDIR/sh_tenants/live_viewcounter.sh"
echo "cd /usr/local/django_projects/podv3 && /home/pod/.virtualenvs/django_pod/bin/python manage.py live_viewcounter --settings=pod.custom.tenants.$NAME.\"$NAME\"_settings  &>> /usr/local/django_projects/podv3/pod/log/cron_viewcounter_$NAME.log 2>&1"  >> "$BASEDIR/live_viewcounter.sh"

echo "FIN"
