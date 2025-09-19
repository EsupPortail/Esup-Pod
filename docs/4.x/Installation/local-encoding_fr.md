---
layout: default
version: 4.x
lang: fr
---

# Gestion de l’encodage en local

Par défaut, l’application exécute les taches d’encodage et de transcription sur la **même machine** que celle sur laquelle elle tourne.

Si l’encodage est effectué sur la même machine que le frontal, leur execution est "threadée" (exécuté dans un sous processus).

Pour configurer ces taches et leur exécution, vous pouvez vous reporter sur le fichier de configuration disponible à cette adresse :

[https://github.com/EsupPortail/Esup-Pod/blob/master/CONFIGURATION_FR.md#configuration-de-lapplication-encodage-et-transcription-de-vid%C3%A9o](https://github.com/EsupPortail/Esup-Pod/blob/master/CONFIGURATION_FR.md#configuration-de-lapplication-encodage-et-transcription-de-vid%C3%A9o)

La configuration se réalise dans votre ```custom/settings_local.py```, en particulier pour les paramètres suivants :

```sh
# Pour ne pas utiliser l’encodage traditionnel déporté
CELERY_TO_ENCODE = False
# Pour ne pas utiliser l’encodage par microservice
USE_REMOTE_ENCODING_TRANSCODING = False
# Fonction appelée pour lancer l’encodage des vidéos
ENCODE_VIDEO = "start_encode"
```
