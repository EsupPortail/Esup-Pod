---
layout: default
version: 4.x
lang: en
---

# Setting up and using a MySQL/MariaDB database

> If you wish to install a MySQL/MariaDB server for Pod, please consult the [Esup-Pod production documentation](production-mode_en).
{: .alert .alert-warning}

This documentation only concerns the configuration and use of an existing MySQL/MariaDB database (typically in a shared environment).

## Installing the libraries

On servers that are to use the MySQL/MariaDB database, the MySQL/MariaDB / Python engine must be installed using the following commands:

```sh
pod@pod:$ sudo apt install -y mariadb-client
pod@pod:$ sudo apt install -y pkg-config python3-dev default-libmysqlclient-dev
pod@pod: $ cd ~/django_projects/podv4
pod@pod:$ workon django_pod4
(django_pod4) pod@pod:~/django_projects/podv4$ pip3 install mysqlclient
```

## Configuring Esup-Pod

If you haven't already done so, you need to specify your database configuration in your `settings_local.py` configuration file:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ vim pod/custom/settings_local.py
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

You then need to run the script in the root directory to create the migration files, then run it to create the database:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ make createDB
```

> Don't forget to create a new superuser:
>
> ```sh
> (django_pod4) pod@pod:~/django_projects/podv4$ python manage.py createsuperuser
> ```
>
{: .alert .alert-warning}
