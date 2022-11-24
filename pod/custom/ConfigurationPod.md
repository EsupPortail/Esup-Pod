# Configuration de la plateforme Esup-Pod

## 1/ Information
La plateforme Esup-Pod se base sur le framework Django écrit en Python. Elle supporte les versions 3.7 3.8 et 3.9 de Python
**Django Version : 3.2 LTS** 
La documentation compléte du framework :
- https://docs.djangoproject.com/fr/3.2/ (ou https://docs.djangoproject.com/en/3.2/)

- l'Ensemble des variables de configuration du framework est accessible à cette adresse : https://docs.djangoproject.com/fr/3.2/ref/settings/

## 2/ Configuration Générale de la plateforme Esup_Pod

SITE_ID = 1
_Valeur par défaut : 1_
>L’identifiant (nombre entier) du site actuel. Peut être utilisé pour mettre en place une instance multi-tenant et ainsi gérer dans une même base de données du contenu pour plusieurs sites.
__ref : https://docs.djangoproject.com/fr/3.2/ref/settings/#site-id__

SECRET_KEY = 'A_CHANGER'
_Valeur par défaut : 'A_CHANGER'_

>La clé secrète d’une installation Django.
>Elle est utilisée dans le contexte de la signature cryptographique, et doit être définie à une valeur unique et non prédictible.

__ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#secret-key__

DEBUG = True
_Valeur par défaut : True_

> Une valeur booléenne qui active ou désactive le mode de débogage.
> Ne déployez jamais de site en production avec le réglage DEBUG activé.

__ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#debug__

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE =  not DEBUG
CSRF_COOKIE_SECURE =  not DEBUG
_Valeur par défaut :  not DEBUG_

> Ces 3 variables servent à sécuriser la plateforme en passant l'ensemble des requetes en https. Idem pour les cookies de session et de cross-sites qui seront également sécurisés
> Il faut les passer à False en cas d'usage du runserver (phase de développement / debugage)

__ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#secure-ssl-redirect__

ALLOWED_HOSTS = ['localhost']
_Valeur par défaut :  ['localhost']_

> Une liste de chaînes représentant des noms de domaine/d’hôte que ce site Django peut servir.
> C’est une mesure de sécurité pour empêcher les attaques d’en-tête Host HTTP, qui sont possibles même avec bien des configurations de serveur Web apparemment sécurisées.

__ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#allowed-hosts__

**Cookie de session**

SESSION_COOKIE_AGE = 14400

> L’âge des cookies de sessions, en secondes.

__ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#session-cookie-age__

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

> Indique s’il faut que la session expire lorsque l’utilisateur ferme son navigateur.

__ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#session-cookie-age__

ADMINS = (('Name', 'adminmail@univ.fr'),)

> Une liste de toutes les personnes qui reçoivent les notifications d’erreurs dans le code.
> Lorsque DEBUG=False et qu’une vue lève une exception, Django envoie un courriel à ces personnes contenant les informations complètes de l’exception.
> Chaque élément de la liste doit être un tuple au format  « (nom complet, adresse électronique) ».
> Exemple : [('John', 'john@example.com'), ('Mary', 'mary@example.com')]
> Dans Pod, les "admins" sont également destinataires des courriels de contact, d'encodage ou de flux rss si la variable CONTACT_US_EMAIL n'est pas renseignée.

__ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#admins__

## 3/ Configuration par application

## 4/ Commande de gestion de l'application
### 4.1/ Creation d'un super utilisateur
