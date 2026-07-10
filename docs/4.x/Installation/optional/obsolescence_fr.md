---
layout: default
version: 4.x
lang: fr
---

# Mise en place de l’obsolescence des vidéos

Nous avons ajouté dans la version 3.1.0 de Pod une date de suppression pour chaque vidéo.
Ce champ date est créé par défaut avec 2 ans de plus que la date d’ajout.
Ces 2 ans sont paramétrables via le setting `DEFAULT_YEAR_DATE_DELETE`

Nous avons ajouté dans la version 4.3 de Pod la possibilité de recalculer la date de suppression de  la vidéo grâce à la commande `respite_launcher` ainsi que la possibilité pour le propriétaire d'une vidéo de décider s'il souhaite prolonger, archiver ou supprimer sa vidéo grâce à une interface dédiée à cela. 

## 1/ Attribut `date_delete`

Lors de l’ajout de la vidéo, quand l’upload est terminé et que la vidéo est enregistrée, cette date est modifiée si l’affiliation du propriétaire est précisée dans la variable `ACCOMMODATION_YEARS`.

Par exemple à Lille, nous avons `ACCOMMODATION_YEARS = {'faculty': 3, 'employee': 3, 'staff': 3}`. Donc pour toute vidéo déposée sur Pod, pour tout le monde c’est 2 ans mais pour les enseignants, personnels et équipe, c’est 3 ans.
En gros, si vous avez `ACCOMMODATION_YEARS = {'student':1}` dans votre fichier de settings, si un étudiant poste une vidéo dans Pod alors sa date de suppression sera égale à un an de plus que sa date d’ajout ; pour tous les autres, ça reste deux ans.

> ⚠️ Attention, il ne faut pas avoir deux fois la variable dans votre fichier de settings ; combinez les 2 précédents ainsi `ACCOMMODATION_YEARS = {'faculty': 3, 'employee': 3, 'staff': 3, 'student':1}`

Pour rappel et par défaut, voici les valeurs possibles pour l’affiliation :

```sh
AFFILIATION = getattr(
    settings, 'AFFILIATION',
    (
        ('student', _('student')),
        ('faculty', _('faculty')),
        ('staff', _('staff')),
        ('employee', _('employee')),
        ('member', _('member')),
        ('affiliate', _('affiliate')),
        ('alum', _('alum')),
        ('library-walk-in', _('library-walk-in')),
        ('researcher', _('researcher')),
        ('retired', _('retired')),
        ('emeritus', _('emeritus')),
        ('teacher', _('teacher')),
        ('registered-reader', _('registered-reader'))
    )
)
```

Donc si vous mettez à jour votre Pod et que vous ne touchez à rien, toutes vos vidéos auront une date de suppression égale à deux ans après la date de mise à jour de votre plateforme.

## 2/ Calcul d'un répit

Nous avons ajouté une commande qui permet de recalculer la valeur de `date_delete` grâce à la commande `respite_launcher` en fonction de critères de la vidéo (type, nombre de vues etc.).

Cette commande peut faire appel à différentes "méthodes de calcul" implémentée dans les fichiers du répertoire `/pod/video/managment/commands/respite_model`

* base.py (par defaut) : ne fait rien
* criteria_model : calcule un age de vidéo en fonction des critères potentiels suivants 
  * id: Id of the video (int)
  * title: Title of the video (string)
  * view_count: count the views of the video (int)
  * view_count_year: Views during the last year (int))
  * is_draft: Tell if it is in draft or not (bool)
  * is_restricted: Tell if video is restricted or not (bool)
  * date_added: upload date of the video (datetime)
  * days_on_platform: number of days on the platforme (int)
  * date_delete: scheduled date of suppression (datetime.date)
  * description: description of the video (string)
  * channels: list of channels where the video is (list)
  * nb_fav: number of favorite the video belong (int)
  * nb_comment: amount of comment on the video (int)
  * duration: 'duration of the video in sec (int)
  * disciplines: Video disciplines (list)
  * type: Video type (Type)
  * themes: themes of the video (list)
  * owner: owner of the video (User)
  * additional_owners: Additional owner of the video (list)
  * categories: categories of the video (list)

Pour activer cette commande il faut :

```sh
USE_RESPITE = True
RESPITE_MODEL = "criteria_model"
```
Et éventuellement préciser les paramétrages à envoyer pour le calcul.
Par exemple, pour le modèle par critère (criteria_model), si je souhaite : 
* donner une durée de vie de 5 ans aux vidéos de type 2 et 4 qui comptent plus de 500 vues 
* et donner une durée de vie de 7 ans aux vidéos de type 3 et 4 qui comptent plus de 1000 vues en tout et plus de 100 vues la dernière année
... j'écrirai :

```sh
RESPITE_MODEL_PARAMETERS = {
    "respite_criteria_parameter": [
        {
            "age": 5,
            "criteria": {
                "type.id": [2], 
                "view_count": 500,
            }
        },
        {
            "age": 7,
            "criteria": {
                "type.id": [3, 4],  
                "view_count": 1000,
                "view_count_year": 100,
            }
        }
    ],
    "archiving_criteria_parameter": {
        ...
    }
}
```

Enfin lancer la commande en mode `--dry` d'abord par précaution
```sh
python manage.py respite_launcher --dry
```

## 3/ Gestion de l’obsolescence et de la notification

Nous avons ajouté une variable `WARN_DEADLINES = getattr(settings, "WARN_DEADLINES", [])`. Elle est donc vide par défaut.

Cette variable doit contenir le nombre de jours avant la date de suppression pour lesquels le propriétaire doit être prévenu.

Par exemple, si vous mettez `WARN_DEADLINES = [60, 30, 7]`, les propriétaires de vidéos recevront un mail 60 jours avant la date de suppression, 30 jours avant et 7 jours avant.

Ensuite 2 possibilités, soit on autorise le propriétaire à choisir la suite à donner via une interface dédiée, soit on ne l'autorise pas. Pour cela, on précise la variable `ENABLE_PAGE_OBSO_MAIL = True/False` (False par défaut).

### Si on n'autorise pas le propriétaire à décider `ENABLE_PAGE_OBSO_MAIL = False`
* s’ils sont « staff », le courriel envoyé leur précisera que leur vidéo va être bientôt supprimée mais qu’ils peuvent modifier la date dans l’interface d’édition avec un lien pour les y conduire.
* s’ils sont « non-staff » (les étudiants), le mail les invitera à contacter les managers de la plateforme (`CONTACT_US_EMAIL` ou `MANAGER` de l’établissement si `USE_ESTABLISHMENT_FIELD` est à True)

Les gestionnaires recevront en récapitulatif la liste des vidéos bientôt supprimées.
Pour les vidéos dont la date de suppression est dépassée, on a ajouté une variable `POD_ARCHIVE_AFFILIATION`. Cette variable est un tableau qui contient toutes les affiliations pour lesquelles on souhaite archiver la vidéo plutôt que de la supprimer. À Lille, `POD_ARCHIVE_AFFILIATION` contient les valeurs suivantes :
`['faculty', 'staff', 'employee', 'affiliate', 'alum', 'library-walk-in', 'researcher', 'retired', 'emeritus', 'teacher', 'registered-reader']`

### Si on autorise le propriétaire à décider `ENABLE_PAGE_OBSO_MAIL = True`
Un courriel sera envoyé aux propriétaires les invitant à faire leur choix via le lien transmis. On pourra préciser ce que l'on autorise et la durée de la prolongation en jours :

```sh
PROLONGATION_GRANTED = True
EXTEND_RESPITE_DAYS = 365
DELETION_GRANTED = True
```

On peut enfin, si on utilise un modèle pour le calcul de répit, affiner l'autorisation d'archiver en précisant des conditions à remplir pour pouvoir archiver. 
Par exemple dans criteria_model on souhaite ne pouvoir archiver que les vidéos qui on suffisamenent de métadonnées. 
Pour cela, on calcule un score et on fixe un minimum à atteindre en "notant" la présence ou non de chaque métadonnées que l'on paramêtre comme suit : 

```sh
RESPITE_MODEL_PARAMETERS = {
    "respite_criteria_parameter": [
        ...
    ],
        "archiving_criteria_parameter": {
        "minimum_expected_score": 7,
        "attribute_scores": {
            "title": 2,
            "description": 3,
            "discipline": 2,
            "tags": 2,
            "date_evt": 1,
        },
        "excluded_title_terms": ["test"],
        "excluded_discipline_terms": ["discipline-2"],
    }
}
```

Si l'archivage n'est pas autorisé l'option n'est pas proposée.

### Archivage

Si l’affiliation du propriétaire est dans cette variable `POD_ARCHIVE_AFFILIATION`, alors :

* Les vidéos sont affectées à un utilisateur précis que l’on peut spécifier via le paramètre `ARCHIVE_OWNER_USERNAME`.
* Elles sont mises en mode brouillon (visible seulement par un superadmin + utilisateur « archive »)
* Le mot `_("archived")` est ajouté à leur titre.
* Enfin, elles sont également ajoutées à l’ensemble « Vidéo à supprimer » (accessible via l’interface d’admin)

> ⚠️ Si, avant d’être archivée, une vidéo a été partagée via un lien contenant son hash code (quelque chose comme `833e349770[...]4b5fdded763`, accessible lorsqu’on partage une vidéo en mode brouillon), alors elle continue à être visible aux personnes disposant de ce lien.

Sinon, les vidéos sont simplement supprimées.

Les gestionnaires recevront deux autres mails chaque jour :

* un avec la liste des **vidéos archivées**
* un autre mail avec la liste des **vidéos supprimées** (identifiant et titre).

De plus, deux fichiers CSV (`deleted.csv` et `archived.csv`) sont créés dans le répertoire log de Django et renseignés avec la liste des vidéos archivées ou supprimées.

## 3/ Mise en route du traitement automatique

Pour lancer le traitement quotidien des vidéos, il faut au préalable ajouter cette variable dans votre fichier de configuration :

```sh
USE_OBSOLESCENCE = True
```

Ensuite, il faut lancer une tâche cron qui passera une fois par jour (ici à 5:00) avec la commande :

```sh
0 5 * * * cd /home/pod/django_projects/podv4 && /home/pod/.virtualenvs/django_pod4/bin/python manage.py check_obsolete_videos
```

## 4/ Traitement automatisé des archives

À partir de la version 3.7.0 de Pod, un script permettant de s’occuper automatiquement des vidéos archivées depuis longtemps est proposé : **create_archive_package**.

Ce script va exporter le fichier vidéo source, ainsi qu’un ensemble de documents et métadonnées associées (sous-titres, notes, commentaires) dans un dossier à part, avant de supprimer la vidéo de Pod.
Un ensemble de paramètres est personnalisable directement dans le fichier `create_archive_package.py` :

```sh
"""CUSTOM PARAMETERS."""
ARCHIVE_ROOT = "/video_archiving"  # Folder where archive packages will be moved
HOW_MANY_DAYS = 365  # Delay before an archived video is moved to ARCHIVE_ROOT
```

Si vous voulez tester la commande sans supprimer de vidéo, vous pouvez la lancer avec l’option `--dry` :

```sh
python manage.py create_archive_package --dry
```

Vous recevrez alors un email récapitulatif de la liste des vidéos qui seraient déplacées.

Lancez ensuite une tâche cron qui passera une fois par semaine (ici les lundis à 6:00) :

```sh
0 6 * * 1 cd /home/pod/django_projects/podv4 && /home/pod/.virtualenvs/django_pod4/bin/python manage.py create_archive_package &>> /var/log/pod/create_archive_package.log
```

## Annexes

### Désarchiver une vidéo

Il peut arriver qu’une vidéo ait été archivée par erreur, que la date d’obsolescence soit mal réglée, etc. Si la vidéo est archivée (et non supprimée), et si vous vous y prenez à temps, la vidéo peut encore être restaurée.

Pour cela, il vous faut préciser l’identifiant de la vidéo, et indiquer l’utilisateur à qui réattribuer la vidéo :
(1er paramètre = video_id, 2e paramètre = user_id)

```sh
pod@pod:~$ python manage.py unarchive_video 1234 5678
```

À partir de la version 3.7.0 de Pod, le 2ᵉ paramètre (user_id) devient facultatif : il vous suffit d’indiquer la vidéo à désarchiver :

```sh
pod@pod:~$ python manage.py unarchive_video 1234
```
