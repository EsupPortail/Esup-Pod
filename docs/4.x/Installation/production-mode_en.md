---
layout: default
version: 4.x
lang: en
---

# Esup-Pod Production Deployment

## MySQL/MariaDB Database

### Installing MariaDB

```sh
sudo apt install mariadb-server mariadb-client
sudo mysql_secure_installation
```

> Warning: You need to modify the file `/etc/mysql/mariadb.conf.d/50-server.cnf`
>
> ```conf
> character-set-server  = utf8
> collation-server      = utf8_general_ci
> ```
>
{: .alert .alert-warning}

You must then create a new database.

```sh
sudo mysqladmin create mydatabase
```

Next, grant privileges on this database to a user specified in your settings file below:

```sh
$ sudo mysql
mysql> GRANT ALL PRIVILEGES ON mydatabase.* TO 'mydatabaseuser'@127.0.0.1 IDENTIFIED BY 'mypassword';
Query OK, 0 rows affected (0.00 sec)

mysql> exit
```

The timezone must be registered in the SQL engine (MySQL or MariaDB) (to be done as MySQL root!)

```sh
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql --database=mysql
```

To use the MySQL/MariaDB database on the frontend server (or a remote server), you need to install the MySQL/Python engine:

```sh
$ sudo apt install pkg-config python3-dev default-libmysqlclient-dev
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ pip3 install mysqlclient
```

### MariaDB Optimization

Your configuration should be adapted to the size of your database. To avoid potential issues during updates, make sure you have at least 256M for the "max_allowed_packet" parameter (increase if your database is larger; set it to the size of your largest table).

`/etc/my.cnf`

```conf
[mysqld]
max_allowed_packet=256M
```

## Esup-Pod Configuration

If not already done, you must specify your database configuration in your settings_local.py configuration file:

```sh
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py
```

```py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '<my_database>',
        'USER': '<my_database_user>',
        'PASSWORD': '<my_database_password>',
        'HOST': '<my_database_host>',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET storage_engine=INNODB, sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1",
            'charset': 'utf8mb4',
        },
    }
}
```

> Replace the various `<my_database_*>` variables according to your environment. For example, for local use, `<my_database_host>` could be replaced by _127.0.0.1_.

Then, run the script at the root to create the migration files, then run them to create the database:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ make createDB
```

> Don’t forget to create a new superuser:
>
> ```sh
> (django_pod4) pod@pod:~/django_projects/podv4$ python manage.py createsuperuser
> ```
>
{: .alert .alert-warning}

## Web Frontend NGINX / UWSGI and Static Files

For more information and explanation than the documentation below, see [the tutorial I followed to set up this solution](https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html#basic-uwsgi-installation-and-configuration)

### Installing and Configuring the NGINX Web Server

Start by installing the NGINX server

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt install nginx
```

Then, edit the file /etc/nginx/sites-enabled/default

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo vim /etc/nginx/sites-enabled/default
```

Find the following line to modify

```conf
[...]
server { listen 80 default_server;
# listen [::]:80 default_server;
[...]
```

> ⚠️ It may also be necessary to replace this step by deleting the `default` file:
>
> ```sh
> (django_pod4) pod@pod:~/django_projects/podv4$ sudo unlink /etc/nginx/sites-enabled/default
> ```
>
{: .alert .alert-warning}

Install NGINX addons

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt install nginx-extras
```

Add the following lines to the nginx configuration file:

`/etc/nginx/nginx.conf`

```conf
http {
[...]
     # Pod Progress Bar: reserve 1MB under the name 'uploads' to track uploads
 upload_progress uploadp 1m;
[...]
}
```

You then need to specify the host for the web server (change the parameters in the `pod_nginx.conf` file if needed).
Also take the opportunity to assign rights to the `www-data` group by editing this pod_nginx.conf file, on the 1st line: `user pod www-data;`.

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ cp pod_nginx.conf pod/custom/.
(django_pod4) pod@pod:~/django_projects/podv4$ vim pod/custom/pod_nginx.conf
(django_pod4) pod@pod:~/django_projects/podv4$ sudo ln -s /usr/local/django_projects/podv4/pod/custom/pod_nginx.conf /etc/nginx/sites-enabled/pod_nginx.conf
(django_pod4) pod@pod:~/django_projects/podv4$ sudo /etc/init.d/nginx restart (or sudo systemctl restart nginx)
```

To start the Nginx service automatically, run the command :

```sh
pod@pod:$ sudo systemctl enable nginx
```

### UWSGI

A configuration file is provided to facilitate the use of UWSGI.

Install the uwsgi module

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo pip3 install uwsgi --break-system-packages
```

Duplicate the template file and edit it to customize the parameters:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ cp pod_uwsgi.ini pod/custom/.
(django_pod4) pod@pod:~/django_projects/podv4$ vim pod/custom/pod_uwsgi.ini
(django_pod4) pod@pod:~/django_projects/podv4$ sudo uwsgi --ini pod/custom/pod_uwsgi.ini --enable-threads --daemonize /usr/local/django_projects/podv4/pod/log/uwsgi-pod.log --uid pod --gid www-data --pidfile /tmp/pod.pid
...
[uWSGI] getting INI configuration from pod/custom/pod_uwsgi.ini
(django_pod4) pod@pod:~/django_projects/podv4$
```

To start the UWSGI service at machine startup:

Create a uwsgi-pod.service file

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo vim /etc/systemd/system/uwsgi-pod.service
```

Add the following:

```conf
[Unit]
Description=Pod uWSGI app
After=syslog.target

[Service]
ExecStart=/usr/local/bin/uwsgi --ini /usr/local/django_projects/podv4/pod/custom/pod_uwsgi.ini \
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

Then enable the service

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo systemctl enable uwsgi-pod
```

To start or stop it:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo systemctl stop uwsgi-pod
(django_pod4) pod@pod:~/django_projects/podv4$ sudo systemctl restart uwsgi-pod
```

> Warning: Don’t forget to collect the "statics" files so they can be served by the NGINX web frontend.
>
> ```sh
> (django_pod4) pod@pod:~/django_projects/podv4$ python manage.py collectstatic
> ```
>
{: .alert .alert-warning}

## Log Rotate

Log files can quickly grow on a production server. Therefore, it is recommended to set up a log rotate system for Esup-Pod logs:

`/etc/logrotate.d/esup-pod`

```conf
/usr/local/django_projects/podv4/pod/log/*.log {
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

Then run the following command to check that it works:

```sh
sudo logrotate -d /etc/logrotate.d/esup-pod
```

## Customizations

Some pages have been automatically pre-generated to make your job easier, but there is still some information to complete.
Notably, the following pages:

* `Home`: <https://pod.univ.fr/admin/flatpages/flatpage/1/change/>
* `/accessibility/`: <https://pod.univ.fr/admin/flatpages/flatpage/3/change/>
* `/legal_notice/`: <https://pod.univ.fr/admin/flatpages/flatpage/2/change/>
