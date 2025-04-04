---
layout: default
version: 4.x
lang: fr
---

# Mise à jour d’Esup-Pod v4

## Avant une MAJ

### Annoncez la maj aux utilisateurs

Dans l’administration de Pod, (https://VOTRE_SERVEUR/admin/main/configuration/), vous trouverez :

Le champ "maintenance_text_sheduled" vous permet de définir un message de maintenance personnalisé.
Le champ "maintenance_sheduled" vous permet d’afficher/masquer (=1 / 0) ce message sur Pod.

### Le jour J

Basculez en mode maintenance (maintenance_mode = 1), cela va désactiver certaines fonctionnalités, et afficher un bandeau "Maintenance en cours. Certaines fonctionnalités sont indisponibles".

## Récupération des sources

```sh
(django_pod4) pod@pod:~/django_projects$ git status
(django_pod4) pod@pod:~/django_projects$ git pull origin master
```

## Build de la stack

```sh
## Force la recompilation des conteneurs (obligatoire au premier lancement ou après un docker-reset)
$ make docker-build
```

Ceci entrainera la suppression des répertoires suivants :

```sh
./pod/log
./pod/static
./pod/node_modules
```

## Mise à jour

Ouvrir un terminal sur le conteneur _pod-back-with-volumes_ ou _pod-dev-with-volumes_ en fonction du type d'installation choisi.

Depuis ce terminal lancer les commandes suivantes

```sh
make upgrade
```

ou les lignes de commandes suivantes

```sh
pip3 install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
cd pod; yarn upgrade; cd ..
# Attention : avant de lancer collectstatic --clear, assurez-vous d’avoir sauvegardé le dossier static/custom si vous y avez mis des fichiers personnalisés.
python manage.py collectstatic --no-input --clear
```

> Vous pouvez directement lancer les commandes depuis la machine hôte grâce à `docker exec`
>
> ```sh
> docker exec -it <container_name> <command>
> # Ex :
> docker exec -it pod-dev-with-volumes make upgrade
> ```
>
> Documentation complète sur docker exec
> <https://docs.docker.com/reference/cli/docker/container/exec/>
>
>
## Mise à jour des paramètres

Après avoir fait une mise à jour d’Esup-Pod, la commande ci-dessous permet de connaitre les nouveaux paramètres par rapport à une version précédente :

Toujours depuis le conteneur _pod-back-with-volumes_ ou _pod-dev-with-volumes_ en fonction du type d'installation choisi.

```sh
python manage.py compareconfiguration *VERSION_PRECEDENTE*
```

par exemple, la commande

```sh
python manage.py compareconfiguration 3.1.1
```

va lister tous les paramètres nouveaux (et ceux plus utilisés) depuis la 3.1.1 jusque la version actuelle.

## Optionnel - Mise à jour d’Opencast Studio

Pour mettre à jour le studio d’Opencast dans votre instance de Esup-Pod, voici les étapes à suivre :

Rendez-vous dans le dossier `opencast-studio/`

Récupérer la dernière version d’Opencast Studio via la commande suivante :

```sh
# Choisir un tag récent car la branche master est sur la version 2.0 qui est un redesign complet
# la liste des tags: https://github.com/elan-ev/opencast-studio/tags
git checkout tags/2023-09-14
git pull
```

Pour les versions jusqu’à 2023-09-14 : régénérez l’Opencast Studio avec la bonne configuration pour Pod via les commandes suivantes :

```sh
export PUBLIC_URL=/studio
npm install
npm run build
```

Pour les versions plus récentes (tags > 2023-10-10), les commandes diffèrent légèrement :

```sh
export PUBLIC_PATH=/studio
npm install
npm run build:release
```

Le répertoire build est alors mis à jour. Renommez-le en studio, puis copier le dans le répertoire pod/custom/static/opencast/

```sh
mkdir -p pod/custom/static/opencast/studio
cp -r build/* pod/custom/static/opencast/studio
```

Finalement, n’oubliez pas de collecter vos fichiers statiques pour la mise en production via la commande :

```sh
python manage.py collectstatic
```

## Redémarrage de la stack

Depuis la machine hôte

```sh
## Lancement sans recompilation des conteneurs, ni suppressions répertoires ./pod/log, ./pod/static, ./pod/node_modules
$ make docker-stop
$ make docker-start
```
