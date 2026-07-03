---
layout: default
version: 4.x
lang: fr
---

# Mise en place de l’enrichissement par l’IA Aristote

> 💡 Cette documentation ne concerne que les versions de ESUP-Pod 3.7.0 et suivantes.

## Introduction

Ce module permet d’enrichir les vidéo avec l’IA Aristote développé par l’école Centrale Supelec ([disi.pages.centralesupelec.fr](https://disi.pages.centralesupelec.fr/innovation/aristote/aristote-website)). Les enrichissements permettent notamment la génération automatique de métadonnées (titre, description et mots clefs), d’une transcription ainsi qu’un Quiz à partir de la bande son de la vidéo.

Techniquement les demandes d’enrichissement se font à l’initiative des propriétaires de vidéo depuis leur page d’édition. Une demande est alors envoyée sur le serveur Aristote avec en paramètre l’URL d’un fichier audio (correspondant à la bande son de la vidéo) et une URL de notification qui sera contactée par Aristote une fois le traitement achevé.

## Pré-requis

Les URL envoyées à Aristote pour la récupération du fichier audio et la notification de traitement doivent être accessibles depuis le monde entier car il n’est actuellement pas possible de filtrer les requêtes effectuées depuis Aristote en réponse aux demandes d’enrichissement. Cela est lié à l’infrastructure d’Aristote (basée sur Kubernetes) qui génère ou supprime automatiquement des serveurs backends en fonction de la charge.

Ces serveurs backends n’ont pas d’IP prévisible et envoie directement les requêtes sans passer par un proxy qui permettrait d’avoir une adresse de provenance fixe et fiable (pouvant être filtrée).

Jusqu’à la version 3.8.1 de POD, ces URL commencent par le nom de domaine du serveur POD qui interroge Aristote. Ce serveur doit donc être accessible au monde entier (ce qui peu poser problème pour les serveurs de test dont l’accès est souvent limité au réseau interne de l’institution qui les héberge).

## Configuration

Pour activer la fonctionnalité il faut renseigner les variables suivantes dans le fichier `pod/custom/settings_local.py` :

- `USE_AI_ENHANCEMENT = True` # Activation de la fonctionnalité
- `AI_ENHANCEMENT_API_URL = 'https://stt.ilaas.fr/api'` # URL pour contacter l’API d’Aristote
- `AI_ENHANCEMENT_CLIENT_ID = 'univ_client_id'`
- `AI_ENHANCEMENT_CLIENT_SECRET = 'xxx-xxx-xxx'` # Submit a request at https://www.ilaas.fr/demande-dacces/ to obtain the identifier and access token.
- `AI_ENHANCEMENT_API_VERSION = 'v1'` # Version de l’API d’Aristote utilisée pour l’enrichissement

Pour obtenir les valeurs à renseigner pour les variables `AI_ENHANCEMENT_CLIENT_ID` et `AI_ENHANCEMENT_CLIENT_SECRET`, il faut faire une demande d’accès à l’API d’Aristote auprès de Centrale Supelec (contact.aristote [at] centralesupelec.fr).

D’autres variables (utiles mais non nécessaires au fonctionnement) peuvent également être ajoutées :

- `AI_ENHANCEMENT_CGU_URL = 'https://disi.pages.centralesupelec.fr/innovation/aristote/aristote-website/utilisation_service'` # URL de la page des conditions d’utilisation de l’IA Aristote
- `AI_ENHANCEMENT_FIELDS_HELP_TEXT = ''` # Personnalisation des termes utilisés pour décrire les champ de saisie sur le formulaire de demande d’enrichissement
- `AI_ENHANCEMENT_TO_STAFF_ONLY = True` # Restriction (ou non) de l’accès à la fonctionnalité aux utilisateurs ayant le statut "Equipe"
