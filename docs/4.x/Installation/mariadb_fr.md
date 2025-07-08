---
layout: default
version: 4.x
lang: fr
---

# Configuration et utilisation d'une base de données MySQL/MariaDB

> Si vous souhaitez installer un serveur MySQL/MariaDB pour Pod, veuillez consulter la [documentation concernant la mise en production d'Esup-Pod](production-mode_fr).
{: .alert .alert-warning}

Cette documentation ne concerne que la configuration et l'utilisation d'une base de données MySQL/MariaDB existante (typiquement dans le cadre d'un environnement mutualisé).

## Installation des librairies

Sur les serveurs devant utiliser la base de données MySQL/MariaDB, il est nécessaire d'installer le moteur MySQL/MariaDB / Python via les commandes suivantes :

```sh
pod@pod:$ sudo apt install -y mariadb-client
pod@pod:$ sudo apt install -y pkg-config python3-dev default-libmysqlclient-dev
pod@pod:$ cd ~/django_projects/podv4
pod@pod:$ workon django_pod4
(django_pod4) pod@pod:~/django_projects/podv4$ pip3 install mysqlclient
```

## Configuration d’Esup-Pod

Si ce n’est pas encore fait, vous devez spécifier la configuration de votre base de données dans votre fichier de configuration settings_local.py :

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

> Remplacer les différentes variables `<my_database_*>` selon votre environnement. Par exemple, en local, `<my_database_host>` pourra être remplacé par _127.0.0.1_.

Il faut ensuite lancer le script présent à la racine afin de créer les fichiers de migration, puis de les lancer afin de créer la base de données :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ make createDB
```

> Ne pas oublier de créer à nouveau un superutilisateur :
>
> ```sh
> (django_pod4) pod@pod:~/django_projects/podv4$ python manage.py createsuperuser
> ```
>
{: .alert .alert-warning}
