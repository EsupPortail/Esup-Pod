---
layout: default
version: 4.x
---

# Installation de Pod v4.x

## Installation standard [WIP]

Les commandes suivantes ont été lancées sur une distribution XXXX

### Environnement

#### Création de l'utilisateur Pod

```sh
user@pod:~$  sudo adduser pod
user@pod:~$  adduser pod sudo
user@pod:~$  su pod
user@pod:~$  cd /home/pod
```

TO BE CONTINUED

## Installation Docker [WIP]

Télécharger et installer Docker https://www.docker.com/

### Configuration

Renommer le fichier .env.dev-exemple en .env.dev et le renseigner.

Vous devez changer les valeurs d'identifiant, mot de passe et courriel.

Pour la variable DOCKER_ENV, vous pouvez choisir entre *light* (1 docker pour Pod avec que l'encodage d'activé) ou *full* (4 docker pour Pod : pod-back, encodage, transcription et xAPI)

Doublon avec ? 
https://github.com/EsupPortail/Esup-Pod/blob/pod_V4/dockerfile-dev-with-volumes/README.adoc
