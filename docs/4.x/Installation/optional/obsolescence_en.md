---
layout: default
version: 4.x
lang: en
---

# Setting up video obsolescence

> ⚠️ Documentation to be tested on Pod v4.

Starting from version 3.1.0 of Pod, a deletion date has been added for each video.
This date field is created by default with 2 years added to the upload date.
These 2 years can be configured using the `DEFAULT_YEAR_DATE_DELETE` setting.

In version 4.3 of Pod, we added the ability to recalculate a video's deletion date using the `respite_launcher` command, as well as the ability for a video's owner to decide whether to extend, archive, or delete their video using a dedicated interface. 

## 1/ Attribute `date_delete`

When adding a video, once the upload is complete and the video is saved, this date is adjusted if the owner’s affiliation is specified in the `ACCOMMODATION_YEARS` variable.

For example, in Lille we have `ACCOMMODATION_YEARS = {'faculty': 3, 'employee': 3, 'staff': 3}`. So for any video uploaded to Pod, the default is 2 years, but for faculty, staff, and employees, it becomes 3 years.
In short, if you have `ACCOMMODATION_YEARS = {'student': 1}` in your settings file, then if a student uploads a video to Pod, its deletion date will be 1 year after the upload date; for everyone else, it remains 2 years.

> ⚠️ Warning: do not define this variable twice in your settings file; instead, combine the two examples as follows:
`ACCOMMODATION_YEARS = {'faculty': 3, 'employee': 3, 'staff': 3, 'student': 1}`

As a reminder, here are the default possible values for affiliation:

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

So, if you update your Pod and change nothing, all your videos will have a deletion date set to two years after the update date of your platform.

## 2/ Calculating a Grace Period

We have added a command that allows you to recalculate the value of `date_delete` using the `respite_launcher` command based on video criteria (type, number of views, etc.).

This command can use different “calculation methods” implemented in the files in the `/pod/video/management/commands/reste_model` directory

* base.py (default): does nothing
* criteria_model: calculates a video’s age based on the following potential criteria 
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

To enable this command, you must:

```sh
USE_RESPITE = True
RESPITE_MODEL = “criteria_model”
```
And, if necessary, specify the settings to be used for the calculation.
For example, for the criteria-based model (criteria_model), if I want to: 
* set a lifespan of 5 years for type 2 and 4 videos with more than 500 views 
* and set a lifespan of 7 years for type 3 and 4 videos with more than 1,000 total views and more than 100 views in the last year
... I would write:
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

Finally, run the command in `--dry` mode first, just to be safe
```sh
python manage.py respite_launcher --dry
```

## 3/ Obsolescence Management and Notifications

We have added a variable `WARN_DEADLINES = getattr(settings, "WARN_DEADLINES", [])`. It is therefore empty by default.

This variable must contain the number of days before the deletion date when the owner must be notified.

For example, if you set `WARN_DEADLINES = [60, 30, 7]`, video owners will receive an email 60 days, 30 days, and 7 days before deletion.

There are then two options: either allow the owner to choose how to proceed via a dedicated interface, or do not allow it. To do this, set the variable `ENABLE_PAGE_OBSO_MAIL = True/False` (False by default).

### If the owner is not allowed to decide (`ENABLE_PAGE_OBSO_MAIL = False`)
* If they are “staff,” the email sent to them will inform them that their video will soon be deleted but that they can change the date in the editing interface, with a link to take them there.
* If they are “non-staff” (students), the email will invite them to contact the platform managers (`CONTACT_US_EMAIL` or the institution’s `MANAGER` if `USE_ESTABLISHMENT_FIELD` is set to True)

Managers will receive a summary list of videos scheduled for deletion.
For videos whose deletion date has passed, we’ve added a variable `POD_ARCHIVE_AFFILIATION`. This variable is an array containing all the affiliations for which we want to archive the video rather than delete it. In Lille, `POD_ARCHIVE_AFFILIATION` contains the following values:
`[‘faculty’, ‘staff’, ‘employee’, ‘affiliate’, ‘alum’, ‘library-walk-in’, ‘researcher’, ‘retired’, ‘emeritus’, ‘teacher’, ‘registered-reader’]`

### If the owner is allowed to set `ENABLE_PAGE_OBSO_MAIL = True`
An email will be sent to owners inviting them to make their choice via the provided link. They can specify what they authorize and the duration of the extension in days:

Finally, if a model is used to calculate the grace period, the archiving authorization can be refined by specifying conditions that must be met in order to archive. 
For example, in `criteria_model`, you might want to allow archiving only for videos that have sufficient metadata. 
To do this, you calculate a score and set a minimum threshold by “scoring” the presence or absence of each metadata field, which you configure as follows: 

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

If archiving is not allowed, the option is not available.

### Archiving

If the owner’s affiliation is listed in `POD_ARCHIVE_AFFILIATION`, then:

* Videos are assigned to a specific user that can be defined using the `ARCHIVE_OWNER_USERNAME` parameter.
* They are set to draft mode (visible only by a superadmin + the “archive” user).
* The word `_("archived")` is added to their title.
* Finally, they are also added to the “Videos to delete” collection (accessible via the admin interface).

> ⚠️ If, before being archived, a video was shared via a link containing its hash code (something like `833e349770[...]4b5fdded763`, available when sharing a draft video), then it remains visible to anyone who has this link.

Otherwise, videos are simply deleted.

Managers will also receive two additional daily emails:

* one with the list of **archived videos**
* another with the list of **deleted videos** (ID and title).

In addition, two CSV files (`deleted.csv` and `archived.csv`) are created in Django’s log directory and filled with the list of archived or deleted videos.

## 3/ Running the Automatic Processing

To enable daily video processing, you must first add this variable to your configuration file:

```sh
USE_OBSOLESCENCE = True
```

Then, you need to schedule a cron job to run once a day (here at 5:00) with the command:

```sh
0 5 * * * cd /home/pod/django_projects/podv4 && /home/pod/.virtualenvs/django_pod4/bin/python manage.py check_obsolete_videos
```

## 4/ Automated Archive Processing

Starting from version 3.7.0 of Pod, a script is provided to automatically handle long-archived videos: **create_archive_package**.

This script exports the source video file along with related documents and metadata (subtitles, notes, comments) into a separate folder, before deleting the video from Pod.
A set of parameters can be customized directly in the `create_archive_package.py` file:

```sh
"""CUSTOM PARAMETERS."""
ARCHIVE_ROOT = "/video_archiving"  # Folder where archive packages will be moved
HOW_MANY_DAYS = 365  # Delay before an archived video is moved to ARCHIVE_ROOT
```

If you want to test the command without deleting any video, you can run it with the `--dry` option:

```sh
python manage.py create_archive_package --dry
```

You will then receive an email with a summary of the videos that would have been moved.

Next, schedule a weekly cron job (here on Mondays at 6:00):

```sh
0 6 * * 1 cd /home/pod/django_projects/podv4 && /home/pod/.virtualenvs/django_pod4/bin/python manage.py create_archive_package &>> /var/log/pod/create_archive_package.log
```

## Appendices

### Unarchiving a Video

It may happen that a video was archived by mistake, that the obsolescence date was misconfigured, etc.
If the video was archived (and not deleted), and if you act in time, it can still be restored.

To do so, you must specify the video ID and the user to whom the video should be reassigned:
(1st parameter = video_id, 2nd parameter = user_id)

```sh
pod@pod:~$ python manage.py unarchive_video 1234 5678
```

From version 3.7.0 of Pod, the 2nd parameter (user_id) becomes optional: you only need to specify the video to be unarchived:

```sh
pod@pod:~$ python manage.py unarchive_video 1234
```
