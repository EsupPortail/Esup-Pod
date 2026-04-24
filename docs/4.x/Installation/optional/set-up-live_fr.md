---
layout: default
version: 4.x
lang: fr
---

# Mise en place d’un direct Live

## Installation d’une nouvelle VM

> 💡 Nous conseillons de mettre en place le direct sur une autre VM que Pod.

Le live se base sur le module RTMP de Nginx.

## Pré-requis

- Installation : documentation réalisée à l’époque sur Debian 9.4 64 bits.

Pour installer nginx en version 1.14, il faut d’abord ajouter les **backports** :

Se placer en tant que root (sudo -s)

```sh
$> vim /etc/apt/sources.list
```

Ajouter la ligne : `deb http://ftp.debian.org/debian stretch-backports main`

Puis faire une mise à jour :

```sh
$> apt update
```

## Installation de nginx

```sh
$> apt-get -t stretch-backports install nginx
```

Ensuite, il faut installer le module nginx-rtmp :

```sh
$> apt-get install libnginx-mod-rtmp
```

## ffmpeg

Pour le multibitrate, il faut installer ffmpeg qui encode en temps réel le flux vidéo :

```sh
$> aptitude install ffmpeg
```

Pour vérifier que tout s’est bien passé, il faut lister le répertoire modules enabled de nginx :

```sh
$> ls -l /etc/nginx/modules-enabled/
```

Vous devez voir mod-rtmp.conf :

```sh
total 16
[...]
lrwxrwxrwx 1 root root 48 oct. 17 12:59 50-mod-rtmp.conf -> /usr/share/nginx/modules-available/mod-rtmp.conf
[...]
```

Ensuite, il faut ajouter l’instruction include rtmp dans le nginx.conf et créer le snippets correspondant :

```sh
$> vim /etc/nginx/nginx.conf
[...]
include /etc/nginx/snippets/rtmp.conf;
[...]
```

Il faut donc ensuite créer le snippet **RTMP** :

```sh
$> vim /etc/nginx/snippets/rtmp.conf
```

### Fichier rtmp.conf originel

Ci-dessous le fichier de configuration originel qui utilise **3 encodages** et n’est pas spécialement optimisé vis-à-vis de la latence (il faut compter entre **15 et 30 secondes de latence** avec cette configuration) :

#### Fichier `/etc/nginx/snippets/rtmp.conf`

```sh
rtmp {
    server {
        listen 1935; # port rtmp par defaut
        chunk_size 4096; # taille des paquets transmis/découpé

         application live { # nom de l’application
            live on;
            #meta copy;
            #record off;

            # publish only from localhost
            allow publish 127.0.0.1; # seulement publier en local
            allow publish all; #tout le monde peut publier
            allow play all; # certaine adresse IP on le droit de lire
            deny publish all; # mettre un deny à la fin pour securiser

            exec ffmpeg -i rtmp://localhost/$app/$name
                -c:v libx264 -preset veryfast -b:v 256k -maxrate 256k -bufsize 512k -vf "scale=480:-2,format=yuv420p" -g 60 -c:a aac -b:a 64k -ar 44100 -f flv rtmp://localhost/show/$name_low
                -c:v libx264 -preset veryfast -b:v 512k -maxrate 512k -bufsize 1024k -vf "scale=720:-2,format=yuv420p" -g 60 -c:a aac -b:a 96k -ar 44100 -f flv rtmp://localhost/show/$name_mid
                -c:v libx264 -preset veryfast -b:v 1024k -maxrate 1024k -bufsize 2048k -vf "scale=1280:-2,format=yuv420p" -g 60 -c:a aac -b:a 128k -ar 44100 -f flv rtmp://localhost/show/$name_high
            >/tmp/ffmpeg.log 2>&1 ;

            exec_publish curl --request PATCH "https://pod.univ.fr/rest/broadcasters/$name/" --header "Content-Type: application/json" --header "Accept: application/json" --user CHANGE_USERNAME:CHANGE-THIS-STATUS-PASSWORD --data "{"status":true}";

            exec_publish_done curl --request PATCH "https://pod.univ.fr/rest/broadcasters/$name/" --header "Content-Type: application/json" --header "Accept: application/json" --user CHANGE_USERNAME:CHANGE-THIS-STATUS-PASSWORD --data "{"status":false}";
        }

        # This application is for splitting the stream into HLS fragments
        application show {
            live on; # Allows live input from above
            meta copy;
            record off;

            hls on; # activation du hls
            hls_path /dev/shm/hls; #chemin des fragment ts mettre dans /dev/shm pour eviter de faire trop travailler le disque
            hls_nested on; # cree un sous repertoire par stream envoye
            hls_fragment 2s; #taille des fragments

            # Instruct clients to adjust resolution according to bandwidth
            hls_variant _low BANDWIDTH=320000; # Low bitrate, sub-SD resolution
            hls_variant _high BANDWIDTH=640000; # High bitrate, higher-than-SD resolution
            hls_variant _src BANDWIDTH=1200000; # Source bitrate, source resolution
        }
    }
}
```

> 💡 Cette configuration est largement éprouvée dans le temps, mais fait consommer plus de ressources (3 encodages) avec une certaine latence au final.

### Fichier rtmp.conf optimisé pour réduire la latence

Ci-dessous le même fichier de configuration qui utilise **2 encodages** et qui est spécialement optimisé vis-à-vis de la latence (il faut compter **moins de 10 secondes de latence** avec cette configuration) .

Ce fichier reprend des éléments de configuration présenté par Ludovic Bouguerra de la société Kalyzée lors de son Webinaire "Mise en place d’une infrastructure de live et réduction de la latence avec Pod" du 23 septembre 2022.

Les éléments de configuration modifiés sont les suivants :

- 2 encodages réalisés
- le preset en ultrafast
- l’option tune zerolatency
- le nombre de keyframes (- g) positionné à 60 (ou 50)

Ce qui donne :

#### Fichier `/etc/nginx/snippets/rtmp.conf` (latence réduite)

```sh
rtmp {
    server {
        listen 1935; # port rtmp par defaut
        chunk_size 4000; # taille des paquets transmis/découpé

         application live { # nom de l’application
            live on;
            #meta copy;
            #record off;

            # publish only from localhost
            allow publish 127.0.0.1; # seulement publier en local
            allow publish all; #tout le monde peut publier
            allow play all; # certaine adresse IP on le droit de lire
            deny publish all; # mettre un deny à la fin pour securiser

            exec ffmpeg -i rtmp://localhost/$app/$name
                -c:v libx264 -preset ultrafast -b:v 512k -tune zerolatency -maxrate 512k -bufsize 1024k -vf "scale=480:-2,format=yuv420p" -g 60 -c:a aac -b:a 96k -ar 44100 -f flv rtmp://localhost/show/$name_low
                -c:v libx264 -preset ultrafast -b:v 1.5M -tune zerolatency -maxrate 1.5M -bufsize 3M -vf "scale=1280:-2,format=yuv420p" -g 60 -c:a aac -b:a 128k -ar 44100 -f flv rtmp://localhost/show/$name_high
            >/tmp/ffmpeg.log 2>&1 ;

            exec_publish curl --request PATCH "https://pod.univ.fr/rest/broadcasters/$name/" --header "Content-Type: application/json" --header "Accept: application/json" --user CHANGE_USERNAME:CHANGE-THIS-STATUS-PASSWORD --data "{"status":true}";

            exec_publish_done curl --request PATCH "https://pod.univ.fr/rest/broadcasters/$name/" --header "Content-Type: application/json" --header "Accept: application/json" --user CHANGE_USERNAME:CHANGE-THIS-STATUS-PASSWORD --data "{"status":false}";
        }

        # This application is for splitting the stream into HLS fragments
        application show {
            live on; # Allows live input from above
            meta copy;
            record off;

            hls on; # activation du hls
            hls_path /dev/shm/hls; #chemin des fragment ts mettre dans /dev/shm pour eviter de faire trop travailler le disque
            hls_nested on; # cree un sous repertoire par stream envoye
            hls_fragment 2s; #taille des fragments
            # Mise en commentaire suite a des problemes en lien avec la publication RTMP de SMP 351
            # hls_max_fragment 3s;
            # hls_playlist_length 10s;

            # Instruct clients to adjust resolution according to bandwidth
            hls_variant _low BANDWIDTH=512000; # Low/Mid bitrate, about sub-SD resolution
            hls_variant _high BANDWIDTH=1500000; # Source bitrate, source resolution
        }
    }
}
```

> 💡 Cette configuration est plus récente, mais fait consommer moins de ressources (2 encodages), avec une latence réduite au final.
>
> ⚠️ Suite à la mise en place en production, il s’est avéré que, lors de la publication RTMP de la part de SMP 351, cette configuration pouvait provoquer une erreur du type " **force fragment split**".
>
> Finalement, en commentant les paramètres suivants, ce problème n’est plus réapparu :
>
> ```sh
> # hls\_max\_fragment 3s;
>
> # hls\_playlist\_length 10s;
> ```

Vous pouvez voir toutes les directives de ce module à cette adresse : [https://github.com/arut/nginx-rtmp-module/wiki/Directives](https://github.com/arut/nginx-rtmp-module/wiki/Directives)

## HTTP

Il faut enfin déclarer la route `hls` pour lire les vidéos :

```sh
$> vim /etc/nginx/sites-enabled/default
```

### Fichier `/etc/nginx/sites-enabled/default`

```sh
server {
  listen 80 default_server;
  root /var/www/html;
  index index.html index.htm index.nginx-debian.html;
  server_name _;
  location / {
      try_files $uri $uri/ =404;
   }
 # path to HLS application service
        location /hls {
            types {
                application/vnd.apple.mpegurl m3u8;
                video/mp2t ts;
            }
            alias /dev/shm/hls;
            add_header Cache-Control no-cache;
            add_header 'Access-Control-Allow-Origin' 'https://pod.univ-machin.fr'; # <--- surtout pas "*" : risque d’injection de code !!!
        }
  add_header 'Access-Control-Allow-Origin' 'https://pod.univ-machin.fr'; # Hotfix pour diffusion depuis un autre serveur <--- surtout pas "*" : risque d’injection de code !!!
}
```

> ⚠️ Si votre frontal POD est en HTTPS il faut configurer Nginx sur le serveur live pour servir du HTTPS et non du HTTP.

## Sur votre instance de POD

Il faut commencer par activer l’application live en ajoutant "live" dans THIRD\_PARTY\_APPS dans le fichier settings\_local.py

```sh
...
THIRD_PARTY_APPS = ["xxx","xxx","live"]
...
```

## Gérer le pilotage du direct et la gestion des enregistrements

Il faut d’abord ajouter le type de type de matériel pour le streaming dont vous disposez (2 choix actuellement).

Cela limitera les choix dans l’admin du site

```sh
...
BROADCASTER_PILOTING_SOFTWARE = ['Wowza', 'SMP']
...
```

Ensuite il faut se rendre dans l’administration de Pod :

- créer un bâtiment
- puis un diffuseur rattaché à ce bâtiment en précisant l’url de lecture du flux de direct

**Important**, selon le type de matériel choisi vous devrez préciser la configuration en json (dans `Paramètres de configuration du pilotage`).

La liste des paramètres à déclarés est proposée lorsque l’on sélectionne un type de matériel.

Voici un exemple de configuration pour les deux matériel supportés.

Cela permet de piloter le démarrage et l’arrêt de l’enregistrement.

### Exemple

```sh
# exemple pour WOWZA:
{
  "server_url":"http://stream01.univ.fr:8087",
  "application":"salles_video",
  "livestream":"sallevideo.stream"
}

# exemple pour SMP:
{
  "server_url":"http://xxx.xxx.xx.x",
  "sftp_port":"22022",
  "user":"compte_admin",
  "password":"mdp_admin",
  "record_dir_path":"/recordings",
  "rtmp_streamer_id":"1",
  "use_opencast":"true"
}
```

### avec WOWZA

Ici le fileSystem sur lequel est stocké le fichier vidéo doit être commun entre Wowza et Pod.

Le paramétrer dans le "DEFAULT\_EVENT\_PATH" du fichier `settings\_local.py`

### avec SMP Extron

si vous utilisez des SMP vous pouvez récupérer le fichier vidéo issue d’un évènement (live) de 2 manières :

#### récupération via SFTP

Pod se connecte au serveur SMP pour récupérer le fichier vidéo et l’encoder en tant que vidéo liée à l’évènement).

Dans la configuration json du diffuseur :

- vérifier que le port est bien déclaré et ouvert entre les 2 serveurs
- `use_opencast` doit être à false
- `rtmp_streamer_id` peut être vide

### #récupération via le module **openCast (studio)**(A partir de 3.7.0)

Le SMP, s’il dispose de la fonctionnalité de push (modèle Extron 351 par exemple), envoie directement le fichier dans le studio de Pod qui va l’encoder et le lier à l’évènement.

Dans la configuration json du diffuseur :

- `use_opencast` doit être à "true"
- `sftp_port` peut être vide
- `rtmp_streamer_id` doit être correctement défini

Pour connaître le `rtmp_streamer_id`, vous pouvez appeler l’url suivante de votre SMP et voir quel streamer est configuré en rtmp (dans le `pub_url`) :

<http://xxx.xxx.xx.x/api/swis/resources?uri=/streamer/rtmp/1&uri=/streamer/rtmp/2&uri=/streamer/rtmp/3&uri=/streamer/rtmp/4&uri=/streamer/rtmp/5&uri=/streamer/rtmp/6>

Vous devez aussi ajouter un Enregistreur (Recorder) dans l’admin de Pod avec l’Ip du SMP (définir un Salt, Login, Password)

Du côté SMP vous devez :

- Activer (ou installer) le plugin Opencast depuis l’interface de gestion du matériel (Configuration -> Advanced Features)
- Paramétrer la publication vers le Opencast de Pod (Scheduled Events -> Publish Settings -> Active Profiles )
  - Opencast Server Address = celle de Pod
  - Username et Password = ceux définis dans le Recorder
- Tester la connexion pour valider les paramètres

## Mise en place du comptage des spectateurs (A partir de 2.7.0 et supérieur)

Pod inclut une fonction qui permet de compter les spectateurs sur un direct en temps réel.

Cette fonctionnalité doit être mise en place de la façon suivante :

- Ajouter une tâche CRON périodique; chaque minute recommandé, mais il est possible d’augmenter ou de diminuer le temps et régler les settings sur pod en conséquence (voir les points suivants ...) :

```sh
bash -c 'export WORKON\_HOME=/home/pod/.virtualenvs; export VIRTUALENVWRAPPER\_PYTHON=/usr/bin/python3.11; cd /home/pod/django_projects/podv4; source /usr/local/bin/virtualenvwrapper.sh; workon django_pod4; python manage.py live_viewcounter'
```

> ⚠️ ATTENTION : Il est possible que vous ayez à modifier cette commande suivant vos chemins d’installation de POD.

- Réglez le setting `HEARTBEAT_DELAY`, celui ci permet de définir le délai entre lequel un client va remonter son "signal" au serveur. Il est par défaut fixé à 45 secondes.
- Réglez le setting `VIEW_EXPIRATION_DELAY`, il permet de définir le délai maximum pour lequel une vue va encore considérée comme présente sur le direct.

> Afin de mieux comprendre ces notions de délais voici un exemple avec les paramètres par défaut : Le client (le terminal sur lequel l’utilisateur est en train de regarder le direct) va remonter un signal au serveur > Pod de manière périodique toutes les **45** (HEARTBEAT\_DELAY) secondes. Chaque **minute** (temps du CRON), une tâche vérifie la validité de chaque spectateur pour déterminer si il est encore présent sur le > direct. Pour cela, elle élimine tout les spectateurs qui n’ont pas remonté de signal depuis **60** (VIEW\_EXPIRATION\_DELAY) secondes.

**A noter** : Il est laissé la possibilité de modifier les délais pour pallier à d’éventuelles pertes de performances à cause de la remontée des vues. Si vous rencontrez des difficultés à ce niveau, n’hésitez pas à doubler les délais. Le comptage sera moins précis en temps réel mais vous gagnerez en nombre de requêtes.

## Diffusion d’un flux video en direct (avec OBS)

Avec **OBS**, dans les paramètres, onglet Flux, je précise ces données :

- **URL** : rtmp://serveur.univ.fr/live
- **Clé de stream** : nico

Dans **Pod**, dans les paramètres de mon diffuseur, dans le champ URL, je vais préciser ceci : <http://serveur.univ.fr/hls/nico.m3u8>

Il faut que le titre court soit le même que le flux/clé de stream (ici **nico**) de manière à ce que le status du live puisse être modifié par l’appel REST ( `exec_publish curl ...)`)

Nous venons donc de créer un flux diffusé en direct accessible en HTML5, multibitrate et adaptatif, voici ce que contient le fichier `nico.m3u8` :

### Fichier `nico.m3u8`

```sh
      #EXTM3U
      #EXT-X-VERSION:3
      #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=320000
      nico_low/index.m3u8

      #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=640000
      nico_high/index.m3u8

      #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1200000
      nico_src/index.m3u8
```
