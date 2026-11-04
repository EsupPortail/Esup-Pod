---
layout: default
version: 4.x
lang: fr
---

# Compatibilités et prérequis

## Quelle noyau et version de Linux puis-je utiliser avec Esup-Pod v4 ?

Esup-Pod v4 a été installé et testé sur des versions Debian 11 / Bullseye, Debian 12 / Bookworm et Debian 13 / Trixie.

> ⚠️ Bien qu’il soit possible d’installer Esup-Pod 4 sur d’autres noyaux, les commandes - affichées dans la documentation - ont été lancées sur une distribution Debian 11, 12 ou 13.

💡Il est recommandé de prendre la dernière version stable de Debian.
Cf. [https://www.debian.org/releases/index.fr.html](https://www.debian.org/releases/index.fr.html)
Au jour de la rédaction de cette documentation, cela serait Debian 12 / Bookworm.
{: .alert .alert-info}

## Quelle version de Python puis-je utiliser avec Esup-Pod v4 ?

| Version d’Esup-Pod | Versions de Python prises en charge |
|--------------------|-------------------------------------|
| 4.0.x et 4.1.x     | 3.9, 3.10, 3.11, 3.12               |
| 4.2.x à 4.4.x      | 3.10, 3.11, 3.12                    |
| 4.5                | 3.11, 3.12                          |
{: .table .table-striped}

💡Il est recommandé de prendre la dernière version stable de Python qui est prise en charge par Django.
Cf. [https://docs.djangoproject.com/en/5.0/faq/install/#what-python-version-can-i-use-with-django](https://docs.djangoproject.com/en/5.0/faq/install/#what-python-version-can-i-use-with-django)
Au jour de la rédaction de cette documentation, cela serait la version 3.12.
{: .alert .alert-info}
