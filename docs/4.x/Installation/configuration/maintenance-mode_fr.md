---
layout: default
version: 4.x
lang: fr
---

# Utilisation du mode maintenance

Depuis la version 2.7.0, Pod intègre un mode maintenance très utile lorsqu'on veut mettre à jour la plateforme. Il permet de rendre indisponible l'ajout de vidéos (et donc le lancement d'encodages) mais de tout de même garder la plateforme accessible à la consultation.

De cette manière, il est possible de laisser les encodages en cours pouvoir se terminer avant de lancer une mise à niveau de pod.

> 💡Information : contrairement à d'autres fonctionnalités de Pod, le mode maintenance s'active par l'administration au lieu d'un setting (cela permet de l'activer sans avoir à redémarrer la plateforme).

Pour activer et personnaliser le mode maintenance, rendez vous dans la section "Configuration" de l'administration :

- Le paramètres `maintenance_mode` permet d'activer le mode maintenance, vous devez le régler sur "1" pour l'activer.
- Le paramètres `maintenance_text_short` est le texte qui sera affiché dans la barre de navigation.
- Le paramètre `maintenance_text_welcome` est le texte affiché sur la page d'accueil de l'application dans un bandeau.
- La paramètre `maintenance_text_disabled` est le texte affiché sur la page vers laquelle est redirigé un utilisateur qui tente d'accéder à une fonctionnalité en maintenance.
