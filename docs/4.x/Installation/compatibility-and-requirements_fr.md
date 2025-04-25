---
layout: default
version: 4.x
lang: fr
---

# Compatibilités et prérequis

## Quelle noyau et version de Linux puis-je utiliser avec Esup-Pod v4 ?

Esup-Pod v4 a été installé et testé sur des versions Debian 11 / Bullseye et Debian 12 / Bookworm.

> ⚠️ Bien qu'il soit possible d'installer Esup-Pod 4 sur d'autres noyaux, les commandes - affichées dans la documentation - ont été lancées sur une distribution Debian 11 ou 12.

💡Il est recommandé de prendre la dernière version stable de Debian.
Cf. [https://www.debian.org/releases/index.fr.html](https://www.debian.org/releases/index.fr.html)
Au jour de la rédaction de cette documentation, cela serait Debian 12 / Bookworm.
{: .alert .alert-info}

## Quelle version de Django puis-je utiliser avec Esup-Pod v4 ?

Esup-Pod v4 fonctionne avec une version 4.2 du framework Django.

💡Il est recommandé de prendre la dernière version stable de Django 4.2.
Cf. [https://www.djangoproject.com/download/#supported-versions](https://www.djangoproject.com/download/#supported-versions)
Au jour de la rédaction de cette documentation, cela serait la version 4.2.20.
{: .alert .alert-info}

## Quelle version de Python puis-je utiliser avec Esup-Pod v4 / Django 4.2 ?

| Version de Django | Versions de Python prises en charge                 |
|-------------------|-----------------------------------------------------|
| 4.2               | 3.8, 3.9, 3.10, 3.11, 3.12 (ajouté en 4.2.8)        |

💡Il est recommandé de prendre la dernière version stable de Python qui est prise en charge par Django.
Cf. [https://docs.djangoproject.com/en/5.0/faq/install/#what-python-version-can-i-use-with-django](https://docs.djangoproject.com/en/5.0/faq/install/#what-python-version-can-i-use-with-django)
Au jour de la rédaction de cette documentation, cela serait la version 3.12.
{: .alert .alert-info}
