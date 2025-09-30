---
layout: default
version: 4.x
lang: fr
---

# Mise en place de l'authentification avec Shibboleth

> ⚠️ Documentation à tester sur un Pod v4.

L’authentification fédérée avec Shibboleth permet d’ouvrir la connexion à votre instance de Pod à toutes personnes possédant un compte dans une fédération Shibboleth. Comme par exemple [la Fédération Education - Recherche de Renater](services.renater.fr)

> De manière pratique, une fois avoir demandé l’authentification sur l’application l’utilisateur sera redirigé vers un service de type WayF (découverte d’établissement) dans lequel il pourra choisir l’établissement dont il provient. Il sera ensuite redirigé vers le système d’authentification de son établissement puis vers l’application Pod dans laquelle il sera connecté avec son compte.

## Installation d’un SP (Service Provider) Shibboleth

Afin de pouvoir mettre en place l’authentification avec Shibboleth, il est nécessaire d’installer un Service Provider. Chaque application “Shibbolétisée” doit posséder son propre SP. À noter qu’il est également nécessaire d’avoir au préalable un IDP (Identity provider) dans votre établissement, si ce n’est pas déjà le cas, un tutoriel existe sur le site de Renater pour en installer un.

Pour installer un SP Shibboleth, vous pouvez suivre les différentes documentations :

* [tutoriel de Renater pour installer un SP version 3 (chapitres jusqu’à 5 ou 6)](https://services.renater.fr/federation/documentation/guides-installation/sp3/chap01)
* [Wiki Shibboleth — Installation (en anglais)](https://wiki.shibboleth.net/confluence/display/SP3/Installation)

Afin de pouvoir utiliser la Fédération Education - Recherche, il est nécessaire d’y inscrire son service. Toute cette procédure est détaillée dans le tutoriel de Renater. Il est conseillé dans un premier temps d’enregistrer son service dans la Fédération de Test, elle permet de tester son SP pour voir si tout fonctionne bien.

## Configuration du Serveur Web

Shibboleth étant prévu pour fonctionner avec Apache2, il s’agit de la méthode recommandée pour le faire fonctionner. Néanmoins, étant donné que Pod utilise Nginx avec uWSGI pour fonctionner, il est nécessaire d’apporter quelques changements dans la configuration.

Le but final est d’avoir un serveur Apache2 en frontal qui (grâce au `mod_shib`) communiquera avec Shibboleth et fournira des routes de connexion/déconnexion au service d’authentification. Ce dernier permettra également d’accéder à l’application par l’utilisation d’un ReverseProxy.

Il s’agit seulement d’une façon de faire, vous n’êtes pas obligé de mettre en place la communication entre Shibboleth et votre application de cette manière. Vous pouvez par exemple [installer Shibboleth du côté Nginx](https://wiki.shibboleth.net) ou encore faire tourner votre instance de Pod en utilisant le mod_wsgi d’Apache et donc sans aucune utilisation de Nginx. Ces méthodes n’ont pas été testées dans ce contexte et sont plus complexes à mettre en place — à vous de choisir celle qui vous convient selon vos besoins.

### Étape 1 : configuration de Nginx

Dans un premier temps, il est nécessaire de changer le port sur lequel Nginx fonctionne (puisqu’on veut que Apache soit frontal). Dans le bloc `server` du fichier `pod_nginx.conf`, il faut donc changer le port d’écoute. Dans cet exemple, le port 8080 a été choisi (mais vous pouvez en choisir un autre). Il est également nécessaire d’activer l’option `proxy_pass_request_header` pour permettre la bonne transmission des headers entre Apache et Nginx. Vous devrez aussi activer `underscores_in_headers`.

```bash
server {
    listen 8080;
    proxy_pass_request_headers on;
    underscores_in_headers on;
    ...
}
```

### Étape 2 : configuration de Apache2

Côté Apache (ou httpd), il faut configurer un `VirtualHost` (ou modifier le `VirtualHost` de base), ou configurer le `httpd.conf` si vous utilisez un serveur httpd.

Selon que vous utilisez HTTP ou la version complète d’Apache, pensez à charger les modules `mod_shib`, `mod_ssl` (si besoin), `mod_proxy` et `mod_proxy_http` pour que l’ensemble des directives ci-dessous fonctionnent.

Exemple :

```bash
<Location />
    ProxyPass https://127.0.0.1:8080/
    ProxyPassReverse http://127.0.0.1:8080/
    AuthType shibboleth
    Require shibboleth
    ShibUseHeaders On
</Location>

<Location /shib/secure>
    # Route de test qu’on peut supprimer par la suite
    ProxyPass !
    AuthType shibboleth
    ShibRequestSetting requireSession 1
    Require shib-session
</Location>

<Location /shib/Shibboleth.sso>
    ProxyPass !
    SetHandler shib
</Location>
```

Si vous devez utiliser `mod_ssl` avec des échanges en HTTPS, vous devrez peut-être utiliser ces options (ou une partie au moins) en complément :

```bash
SSLProxyEngine On
SSLProxyVerify none
SSLProxyCheckPeerCN off
SSLProxyCheckPeerName off
SSLProxyCheckPeerExpire off
ProxyRequests Off
ProxyPreserveHost On
```

> ⚠️ Pensez également à tester votre installation de Shibboleth en vous rendant sur `/shib/secure` : il s’agit d’une route de test qui vous permet de vérifier le bon fonctionnement de votre SP.

### Étape 3 : configuration de Pod

Pour prendre en charge l’authentification avec Shibboleth dans Pod, il faut paramétrer 5 settings:

```bash
USE_SHIB = True  # Active l'authentification Shibboleth dans la page de connexion
SHIB_NAME = "Fédération de Test"  # Précise le nom de la fédération d’identité qui sera affichée
SHIBBOLETH_ATTRIBUTE_MAP = {
    "HTTP_REMOTE_USER": (True, "username"),
    "HTTP_DISPLAYNAME": (True, "first_name"),
    "HTTP_DISPLAYNAME": (True, "last_name"),
    "HTTP_MAIL": (False, "email"),
}
REMOTE_USER_HEADER = "HTTP_REMOTE_USER"  # Nom d’en-tête pour identifier l’utilisateur connecté
SHIB_URL = "https://univ-lr.fr/shib/Shibboleth.sso/Login"
SHIB_LOGOUT_URL = "https://univ-lr.fr/shib/Shibboleth.sso/Logout"
```

Pensez également à ajouter l’authentification Shibboleth à l’attribut `AUTH_TYPE` :

```bash
AUTH_TYPE = (('local', ('local')), ('CAS', 'CAS'), ('Shibboleth', 'Shibboleth'))
```

Une fois la configuration dans Pod effectuée, l’authentification Shibboleth s’affichera dans la page de connexion :

![Authentification Shibboleth](shibboleth_screens/shibboleth1.png)

>💡Il est totalement possible de faire cohabiter différents types d’authentification : vous pouvez très bien activer CAS, Shibboleth et l’authentification locale en même temps.

> À partir de là, l’authentification Shibboleth devrait fonctionner correctement pour Pod. Si des erreurs subsistent, pensez à regarder les logs de Shibboleth-SP (`/var/log/shibboleth`) ou du côté de l’IdP pour trouver la source.

> Si vous constatez un message d’erreur *502 Bad Request*, vérifiez la taille des en-têtes renvoyés. Pensez à réduire le fichier `attribute-map.xml` ou augmenter dans la configuration uWSGI `max_vars` (qui est par défaut à 64) afin de l’ajuster au nombre d’en-têtes reçus.
