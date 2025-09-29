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

## 1/ Attribute `date_delete`

When adding a video, once the upload is complete and the video is saved, this date is adjusted if the owner’s affiliation is specified in the `ACCOMMODATION_YEARS` variable.

For example, in Lille we have `ACCOMMODATION_YEARS = {'faculty': 3, 'employee': 3, 'staff': 3}`. So for any video uploaded to Pod, the default is 2 years, but for faculty, staff, and employees, it becomes 3 years.
In short, if you have `ACCOMMODATION_YEARS = {'student': 1}` in your settings file, then if a student uploads a video to Pod, its deletion date will be 1 year after the upload date; for everyone else, it remains 2 years.

> ⚠️ Warning: do not define this variable twice in your settings file; instead, combine the two examples as follows:
`ACCOMMODATION_YEARS = {'faculty': 3, 'employee': 3, 'staff': 3, 'student': 1}`

As a reminder, here are the default possible values for affiliation:

```bash
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

## 2/ Obsolescence Management and Notifications

We have added a variable `WARN_DEADLINES = getattr(settings, "WARN_DEADLINES", [])`. It is therefore empty by default.

This variable must contain the number of days before the deletion date when the owner must be notified.

For example, if you set `WARN_DEADLINES = [60, 30, 7]`, video owners will receive an email 60 days, 30 days, and 7 days before deletion.

Then:

* if they are “staff,” the email will inform them that their video will soon be deleted but that they can modify the date in the edit interface (a link will be included).
* if they are “non-staff” (students), the email will invite them to contact the platform managers (`CONTACT_US_EMAIL` or the institution’s `MANAGER` if `USE_ESTABLISHMENT_FIELD` is set to True).

Managers will also receive a summary with the list of videos about to be deleted.
For videos whose deletion date has passed, a variable `POD_ARCHIVE_AFFILIATION` has been added. This variable is an array containing all affiliations for which videos should be archived instead of deleted. In Lille, `POD_ARCHIVE_AFFILIATION` contains the following values:
`['faculty', 'staff', 'employee', 'affiliate', 'alum', 'library-walk-in', 'researcher', 'retired', 'emeritus', 'teacher', 'registered-reader']`

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

```bash
USE_OBSOLESCENCE = True
```

Then, you need to schedule a cron job to run once a day (here at 5:00) with the command:

```bash
0 5 * * * cd /home/pod/django_projects/podv4 && /home/pod/.virtualenvs/django_pod4/bin/python manage.py check_obsolete_videos
```

## 4/ Automated Archive Processing

Starting from version 3.7.0 of Pod, a script is provided to automatically handle long-archived videos: **create_archive_package**.

This script exports the source video file along with related documents and metadata (subtitles, notes, comments) into a separate folder, before deleting the video from Pod.
A set of parameters can be customized directly in the `create_archive_package.py` file:

```bash
"""CUSTOM PARAMETERS."""
ARCHIVE_ROOT = "/video_archiving"  # Folder where archive packages will be moved
HOW_MANY_DAYS = 365  # Delay before an archived video is moved to ARCHIVE_ROOT
```

If you want to test the command without deleting any video, you can run it with the `--dry` option:

```bash
python manage.py create_archive_package --dry
```

You will then receive an email with a summary of the videos that would have been moved.

Next, schedule a weekly cron job (here on Mondays at 6:00):

```bash
0 6 * * 1 cd /home/pod/django_projects/podv4 && /home/pod/.virtualenvs/django_pod4/bin/python manage.py create_archive_package &>> /var/log/pod/create_archive_package.log
```

## Appendices

### Unarchiving a Video

It may happen that a video was archived by mistake, that the obsolescence date was misconfigured, etc.
If the video was archived (and not deleted), and if you act in time, it can still be restored.

To do so, you must specify the video ID and the user to whom the video should be reassigned:
(1st parameter = video_id, 2nd parameter = user_id)

```bash
pod@pod:~$ python manage.py unarchive_video 1234 5678
```

From version 3.7.0 of Pod, the 2nd parameter (user_id) becomes optional: you only need to specify the video to be unarchived:

```bash
pod@pod:~$ python manage.py unarchive_video 1234
```
