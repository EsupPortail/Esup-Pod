# Installation

Les commandes suivantes ont été lancées sur une distribution Debian 9.4 "stretch".

## Environnement
### Creation de l'utilisateur Pod
```
$ sudo adduser pod
$ adduser pod sudo
$ su pod
```
### Création de l'environnement virtuel

```
pod@pod:~$ sudo pip install virtualenvwrapper
```

A la fin du bashrc, il faut ajouter ces deux lignes :

```
pod@pod:~$ vim .bashrc
[...]
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
```

Puis prendre en charge ces modifications :

```
pod@pod:$ source .bashrc
```

Et enfin créer l'environnement virtuel :

```
pod@pod:~$ mkvirtualenv --system-site-packages --python=/usr/bin/python3 django_pod 
```

### Récupération des sources

Concernant l'emplacement du projet, je conseille de le mettre dans /usr/local/django_projects

```
(django_pod)pod@pod:~$ sudo mkdir /usr/local/django_projects
```

Vous pouvez faire un lien symbolique dans votre home pour arriver plus vite dans le répertoire django_projects:

```
(django_pod)pod@pod:~$ ln -s /usr/local/django_projects django_projects
```

Placez vous dans le répertoire django_projects

```
(django_pod)pod@pod:~$ cd django_projects
(django_pod)pod@pod:~/django_projects$
```

Donnez les droits à l'utilisateur Pod de lire et d'écrire dans le répertoire :

```
(django_pod) pod@pod:~/django_projects$ sudo chown pod:pod /usr/local/django_projects
```

Vous pouvez enfin récupérer les sources :

Attention, si vous devez utiliser un proxy, vous pouvez le spécifier avec cette commande :

```
(django_pod) pod@pod:~/django_projects$ git config --global http.proxy http://PROXY:PORT
```

la récupération des sources de la V2 se font via cette commande : **git clone https://github.com/esupportail/podv2.git**

```
(django_pod) pod@pod1-test:~/django_projects$ git clone https://github.com/esupportail/podv2.git
Clonage dans 'podv2'...
remote: Counting objects: 4578, done.
remote: Compressing objects: 100% (378/378), done.
remote: Total 4578 (delta 460), reused 564 (delta 348), pack-reused 3847
Réception d'objets: 100% (4578/4578), 4.40 MiB | 3.88 MiB/s, fait.
Résolution des deltas: 100% (3076/3076), fait.
(django_pod) pod@pod1-test:~/django_projects$ cd podv2/
```

## Installation
### Installation de toutes les librairies python :

```
(django_pod) pod@pod:~/django_projects/podv2$ pip install -r requirements.txt
```

De même, si vous devez utiliser un proxy :

```
$> pip install --proxy="PROXY:PORT" -r requirements.txt
```

### FFMPEG
Pour l'encodage des vidéos et la creation des vignettes, il faut installer **ffmpeg**, **ffmpegthumbnailer** et **imagemagick**

```
(django_pod) pod@pod:~/django_projects/podv2$ sudo aptitude install ffmpeg
(django_pod) pod@pod:~/django_projects/podv2$ sudo aptitude install ffmpegthumbnailer
(django_pod) pod@pod:~/django_projects/podv2$ sudo aptitude install imagemagick
```

### Elasticsearch

Pour utiliser Elasticsearch, il faut avoir java8 sur sa machine :

```
(django_pod) pod@pod:~/django_projects/podv2$ sudo aptitude install openjdk-8-jre
```

Puis pour installer Elasticsearch sur Debian en utilsant les paquets, il faut suivre les instructions  situées à cette adresse : <https://www.elastic.co/guide/en/elasticsearch/reference/current/deb.html>

Voici :

```
django_pod) pod@pod:~/django_projects/podv2$ wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
OK
(django_pod) pod@pod:~/django_projects/podv2$ sudo apt-get install apt-transport-https
(django_pod) pod@pod:~/django_projects/podv2$ echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-6.x.list
deb https://artifacts.elastic.co/packages/6.x/apt stable main
(django_pod) pod@pod:~/django_projects/podv2$ sudo apt-get update && sudo apt-get install elasticsearch
```

Ensuite il faut paramétrer l'instance :

```
(django_pod) pod@pod:~/django_projects/podv2$ sudo vim /etc/elasticsearch/elasticsearch.yml
```

Pour préciser trois valeurs :

- **cluster.name**: pod-application
- **node.name**: pod-1
- **discovery.zen.ping.unicast.hosts**: ["127.0.0.1"]

Il faut enfin le lancer et vérifier son bon fonctionnement :

```
(django_pod) pod@pod:~/django_projects/podv2$ sudo /etc/init.d/elasticsearch start
(django_pod) pod@pod:~/django_projects/podv2$ curl -XGET "127.0.0.1:9200"
{
  "name" : "pod-1",
  "cluster_name" : "pod-application",
  "cluster_uuid" : "lG2pQ219SHePd4axTKBNZA",
  "version" : {
    "number" : "6.2.4",
    "build_hash" : "ccec39f",
    "build_date" : "2018-04-12T20:37:28.497551Z",
    "build_snapshot" : false,
    "lucene_version" : "7.2.1",
    "minimum_wire_compatibility_version" : "5.6.0",
    "minimum_index_compatibility_version" : "5.0.0"
  },
  "tagline" : "You Know, for Search"
}
```

Pour utiliser la recherche dans Pod, nous allons avoir besoin également du plugin ICU:

```
(django_pod) pod@pod:~/django_projects/podv2$ cd /usr/share/elasticsearch/
(django_pod) pod@pod:/usr/share/elasticsearch$ sudo bin/elasticsearch-plugin install analysis-icu
-> Downloading analysis-icu from elastic
[=================================================] 100%   
-> Installed analysis-icu
(django_pod) pod@pod:/usr/share/elasticsearch$ sudo /etc/init.d/elasticsearch restart
[ ok ] Restarting elasticsearch (via systemctl): elasticsearch.service.
```

#### Creation de l'index Pod
Nous pouvons enfin vérifier le bon fonctionnement de l'ensemble (l'erreur affichée lors de la deletion est normal puisque l'indice n'existe pas mais nous devons supprimer avant de créer un index dans ES):

```
(django_pod) pod@pod:~/django_projects/podv2$ python manage.py create_pod_index
DELETE http://127.0.0.1:9200/pod [status:404 request:0.140s]
An error occured during index video deletion: 404-index_not_found_exception : no such index
Successfully create index Video
(django_pod) pod@pod:~/django_projects/podv2$ curl -XGET "127.0.0.1:9200/pod/_search"
{"took":35,"timed_out":false,"_shards":{"total":2,"successful":2,"skipped":0,"failed":0},"hits":{"total":0,"max_score":null,"hits":[]}}
```

## Mise en route
### Base de données
Lancer le script présent à la racine afin de créer les fichier de migration, puis de les lancer afin de créer la base de données

```
(django_pod) pod@Pod:~/django_projects/podv2$ sh create_data_base.sh 
```
### SuperUtilisateur

Il faut créer un premier utilisateur qui aura tous les pouvoirs sur votre instance.

```
(django_pod) pod@Pod:~/django_projects/podv2$ python manage.py createsuperuser
```

### Tests

Enfin afin de vérifier que votre instance est opérationnelle, il faut lancer les tests unitaires :

```
(django_pod) pod@Pod:~/django_projects/podv2$ python manage.py test
```

### Serveur de développement

Le serveur de développement permet de tester vos futurs modifications facilement.

N'hésitez pas à lancer le serveur de développement pour vérifier vos modifications au fur et à mesure.

À ce niveau, vous devriez avoir le site en français et en anglais et voir l'ensemble de la page d'accueil.

```
(django_pod) pod@Pod:~/django_projects/podv2$ python manage.py python manage.py runserver ADRESSE_IP/NOM_DNS:8080
```

### - Attention -

------
> ### Avant la mise en production, il faut vérifier le fonctionnement de la plateforme dont l'ajout d'une vidéo, son encodage et sa suppression.
> 
> ### Attention, pour ajouter une vidéo, il doit y avoir au moins un type de vidéo disponible. Si vous avez correctement peuplé votre base de données avec le fichier initial_data.json vous devez au moins avoir other/autres.
> 
> ### il faut vérifier l'authentification CAS, le moteur de recherche etc. 
> 
> ### ==> Voir paramétrage / customization
      
------

