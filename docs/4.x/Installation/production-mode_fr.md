---
layout: default
version: 4.x
lang: fr
---

# Mise en production d’Esup-Pod

## Base de données MySQL/MariaDB

### Installation de MariaDB

```sh
sudo apt install mariadb-server mariadb-client
sudo mysql_secure_installation
```

> Attention il faut modifier le fichier `/etc/mysql/mariadb.conf.d/50-server.cnf`
>
> ```conf
> character-set-server  = utf8
> collation-server      = utf8_general_ci
> ```
>
{: .alert .alert-warning}

Vous devez ensuite créer une nouvelle base de données.

```sh
sudo mysqladmin create mydatabase
```

Il faut ensuite donner les droits à cette base à un utilisateur renseigné dans votre fichier de settings ci-après

```sh
$ sudo mysql
mysql> GRANT ALL PRIVILEGES ON mydatabase.* TO 'mydatabaseuser'@127.0.0.1 IDENTIFIED BY 'mypassword';
Query OK, 0 rows affected (0.00 sec)

mysql> exit
```

Le timezone doit être enregistré dans le moteur SQL (Mysql ou mariadb) (à faire en tant que root mysql !)

```sh
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql --database=mysql
```

Pour utiliser la base de données MySQL/MariaDB sur le serveur frontal (ou sur un serveur distant), il faut installer le moteur MySql/Python :

```sh
$ sudo apt install pkg-config python3-dev default-libmysqlclient-dev
(django_pod) pod@pod:/usr/local/django_projects/pod$ pip3 install mysqlclient
```

### Optimisation de MariaDB

Votre configuration doit être adaptée à la taille de votre base de donnée. Pour éviter d'éventuels souci lors des mises à jour, je vous invite à vous assurer que vous avez au minimum 256M pour le paramètre "max_allowed_packet" (voir plus si votre base de données est plus importante. Il faut indiquer la taille de votre plus grosse table)

`/etc/my.cnf`

```conf
[mysqld]
max_allowed_packet=256M
```

## Configuration d’Esup-Pod

Si ce n’est pas encore fait, vous devez spécifier la configuration de votre base de données dans votre fichier de configuration settings_local.py :

```sh
(django_pod) pod@pod:/usr/local/django_projects/pod$ vim pod/custom/settings_local.py
```

```py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mydatabase',
        'USER': 'mydatabaseuser',
        'PASSWORD': 'mypassword',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET storage_engine=INNODB, sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1",
            'charset': 'utf8mb4',
        },
    }
}
```

Il faut ensuite relancer le script présent à la racine afin de créer les fichiers de migration, puis de les lancer afin de créer la base de données :

```sh
(django_pod) pod@Pod:~/django_projects/pod$ make createDB
```

> Ne pas oublier de créer à nouveau un superutilisateur
>
> ```sh
> (django_pod) pod@Pod:~/django_projects/pod$ python manage.py createsuperuser
> ```
>
{: .alert .alert-warning}

## Frontal Web NGINX / UWSGI et fichiers statiques

Pour plus de renseignement, d'explication que la documentation ci-dessous, voir [le tutoriel que j'ai suivi pour mettre en place cette solution](https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html#basic-uwsgi-installation-and-configuration)

### Installation du serveur Web NGINX et paramétrage

Commencer par installer le serveur NGINX

```sh
(django_pod) pod@Pod:~/django_projects/pod$ sudo apt install nginx
```

Ensuite, modifier le fichier /etc/nginx/sites-enabled/default

```sh
(django_pod) pod@Pod:~/django_projects/pod$ sudo vim /etc/nginx/sites-enabled/default
```

Rechercher la ligne ci-dessous à modifier

```conf
[...]
server { listen 80 default_server;
# listen [::]:80 default_server;
[...]
```

Installer les addons de NGINX

```sh
(django_pod) pod@Pod:~/django_projects/pod$ sudo apt install nginx-extras
```

Rajouter les lignes ci-dessous dans le fichier de configuration de nginx :

`/etc/nginx/nginx.conf`

```conf
http {
[...]
     # Pod Progress Bar : reserve 1MB under the name 'uploads' to track uploads
 upload_progress uploadp 1m;
[...]
}
```

Il faut ensuite spécifier le host pour le serveur web (changer si besoin les paramètres dans le fichier pod_nginx.conf) :

```sh
(django_pod) pod@Pod:~/django_projects/pod$ cp pod_nginx.conf pod/custom/.
(django_pod) pod@Pod:~/django_projects/pod$ vim pod/custom/pod_nginx.conf
(django_pod) pod@Pod:~/django_projects/pod$ sudo ln -s /usr/local/django_projects/podv3/pod/custom/pod_nginx.conf /etc/nginx/sites-enabled/pod_nginx.conf
(django_pod) pod@Pod:~/django_projects/pod$ sudo /etc/init.d/nginx restart
```

### UWSGI

Un fichier de configuration est fourni pour faciliter l’usage d'UWSGI.

Installer le module uwsgi

```sh
(django_pod) pod@Pod:~/django_projects/pod$ sudo pip3 install uwsgi
```

Dupliquez le fichier modèle et éditez-le pour personnaliser les paramètres :

```sh
(django_pod) pod@Pod:~/django_projects/pod$ cp pod_uwsgi.ini pod/custom/.
(django_pod) pod@Pod:~/django_projects/pod$ vim pod/custom/pod_uwsgi.ini
(django_pod) pod@Pod:~/django_projects/pod$ sudo uwsgi --ini pod/custom/pod_uwsgi.ini --enable-threads --daemonize /usr/local/django_projects/podv3/pod/log/uwsgi-pod.log --uid pod --gid www-data --pidfile /tmp/pod.pid
...
[uWSGI] getting INI configuration from pod/custom/pod_uwsgi.ini
(django_pod) pod@Pod:~/django_projects/pod$
```

Pour lancer le service UWSGI au démarrage de la machine :

Créer un fichier uwsgi-pod.service

```sh
(django_pod) pod@Pod:~/django_projects/pod$ sudo vim /etc/systemd/system/uwsgi-pod.service
```

Y ajouter :

```conf
[Unit]
Description=Pod uWSGI app
After=syslog.target

[Service]
ExecStart=/usr/local/bin/uwsgi --ini /usr/local/django_projects/podv3/pod/custom/pod_uwsgi.ini \
        --enable-threads \
        --pidfile /tmp/pod.pid
ExecStop=/usr/local/bin/uwsgi --stop /tmp/pod.pid
User=pod
Group=www-data
Restart=on-failure
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target
```

Il faut ensuite activer le service

```sh
(django_pod) pod@Pod:~/django_projects/pod$ sudo systemctl enable uwsgi-pod
```

Pour le lancer ou l’arrêter :

```sh
(django_pod) pod@Pod:~/django_projects/pod$ sudo systemctl stop uwsgi-pod
(django_pod) pod@Pod:~/django_projects/pod$ sudo systemctl restart uwsgi-pod
```

> Attention, il faut penser à collecter les fichiers "statics" pour qu'ils soient servis par le frontal web NGINX.
>
> ```sh
> (django_pod) pod@Pod:~/django_projects/pod$ python manage.py collectstatic
> ```
>
{: .alert .alert-warning}

## Log Rotate

Les fichiers de log peuvent vite grossir sur un serveur en production. Aussi, je vous invite à mettre en place un système de log rotate pour les logs d'Esup-Pod :

`/etc/logrotate.d/esup-pod`

```conf
/usr/local/django_projects/podv3/pod/log/*.log {
    su pod www-data
    daily
    missingok
    rotate 14
    nocompress
    delaycompress
    notifempty
    create 0640 pod www-data
    sharedscripts
    postrotate
        systemctl restart uwsgi-pod >/dev/null 2>&1
    endscript
}
```

Puis lancez la commande suivante pour vérifier que ça fonctionne :

```sh
sudo logrotate -d /etc/logrotate.d/esup-pod
```
