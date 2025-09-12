---
layout: default
version: 4.x
lang: fr
---

# Optimisation Web

> 💡Documentation à revoir pour la v4.

Afin d'optimiser au mieux nos serveurs pod, je vous invite à partager ce que chacun a pu mettre en place pour optimiser son serveur.

## Avant propos

Si vous souhaitez savoir ou se situe votre serveur Pod en terme d'optimisation, je vous propose de le tester par exemple via PageSpeed :

[https://developers.google.com/speed/pagespeed/insights](https://developers.google.com/speed/pagespeed/insights)

À titre de référence, le serveur [pod.univ-lille.fr](http://pod.univ-lille.fr) donne les scores suivants en février 2021 (pod v2.7.3.1) :

- Page d'accueil : mobile 66% / desktop 88%
- Sur une vidéo : mobile 31% / desktop 71%

(plus le score est élevé, mieux c'est)

## À Nice

Avant toute optimisation, on avait les résultats suivants :

- Pour un lien vers une vidéo : mobile 22% / desktop 57%
- page d'accueil : on avait pas regardé ![(wink)](http://www.esup-portail.org/wiki/s/9j7max/9111/1h7j1tb/_/images/icons/emoticons/wink.svg)

Au niveau du Nginx, voici ce qu'on a fait :

1. ### Indiquer à nginx de servir des versions compressées des fichiers statics

Avec cela, lorsque nginx trouve un fichier `file.css.gz` dans le dossier static, il l'envoie à la place de la version standard (le navigateur fera la décompression)

**pod_nginx.conf**

```bash
location /static {
    gzip_static  on;
    gzip_types text/plain application/xml text/css text/javascript application/javascript image/svg+xml;
    [...]
}
```

Pour que cela marche bien, il faut bien sûr avoir des fichier ".gz", on lance donc manuellement un script shell :

**compress_static.sh**

```bash
#!/bin/bash
# Generate compressed versions of all statics files to be served by nginx
cd podv4/pod/static/
for file in $(find . -type f)
do
    if [[ $file =~ .*\.(css|js|svg)$ ]]
    then
        gzip -fk "$file"
    fi
done
```

==\> cette étape pourrait être inutile à partir du moment ou on installe [https://github.com/whs/django-static-compress](https://github.com/whs/django-static-compress)

### 2. Activer la compression à la volée par nginx des contenus textuels non statics

pour optimiser la bande passante, on peux aussi améliorer les perfs en demandant à nginx de compresser à la volée les contenus textuels. voici ce qu'on a ajouté à pod\_nginx.conf :

**pod_nginx.conf**

```bash
    # Django media
    location /media {
        gzip on;
        gzip_types text/vtt;
    [...]
    }
    [...]
    # Finally, send all non-media requests to the Django server.
    location / {
        gzip on;
        uwsgi_pass  django;
    [...]
    }
```

nb : pour que les fichiers vtt soient reconnus comme texte, on les a ajoutés comme "text/vtt" dans `/etc/ningx/mime.types`

**3. Mise en cache**

Nous avons défini la politique de mise en cache suivante (1 an sur /media, 60j sur /static) :

Pour plus d'infos sur l'importance de définir des "expires", je vous invite à suivre cette doc : [Éviter les mises en cache de durée imprévisible des fichiers statiques](http://www.esup-portail.org/wiki/spaces/DOC/pages/967737345/%C3%89viter+les+mises+en+cache+de+dur%C3%A9e+impr%C3%A9visible+des+fichiers+statiques)

**pod_nginx.conf**

```bash
location /media {
    expires 1y;
    add_header Cache-Control "public";
    [...]
}
location /static {
    expires 60d;
    add_header Cache-Control "public";
    [..]
}
```

==\> avec l'ensemble de ces changements, on est passé d'un score de 22/57 à 40/77 (mobile/desktop) à Nice

Sur la page d'accueil, on est aujourd'hui à 81%/95%.
