---
layout: default
version: 4.x
lang: en
---

- [BigBlueButton Infrastructure Migration, with Pod Support](#bigbluebutton-infrastructure-migration-with-pod-support)
  - [Context](#context)
  - [Impacts](#impacts)
  - [Constraints](#constraints)
  - [Provided Solution](#provided-solution)
- [Architecture of the Solution](#architecture-of-the-solution)
  - [Plugin `bbb-recorder`](#plugin-bbb-recorder)
    - [Functioning of `bbb-recorder`](#functioning-of-bbb-recorder)
    - [Installation of `bbb-recorder` on Encoding Servers](#installation-of-bbb-recorder-on-encoding-servers)
      - [Installation of Chrome and Prerequisites](#installation-of-chrome-and-prerequisites)
      - [Effective Installation](#effective-installation)
    - [Configuration of `bbb-recorder`](#configuration-of-bbb-recorder)
  - [Configuration](#configuration)
    - [Configuration in Pod](#configuration-in-pod)
    - [Script `migrate_bbb_recordings`](#script-migrate_bbb_recordings)
      - [Script Functioning](#script-functioning)
      - [Internal Script Configuration](#internal-script-configuration)
      - [Format of `DB_PARAMS`](#format-of-db_params)
      - [Script Arguments](#script-arguments)
      - [Examples and Use Cases](#examples-and-use-cases)
        - [Initialization](#initialization)
        - [1. Claiming All Recordings (Simulation)](#1-claiming-all-recordings-simulation)
        - [2. Claiming the Last 2 Recordings (Simulation)](#2-claiming-the-last-2-recordings-simulation)
        - [3. External Video Import with Moodle Database (Simulation)](#3-external-video-import-with-moodle-database-simulation)
        - [4. External Video Import without Moodle Database (Last 10, Simulation)](#4-external-video-import-without-moodle-database-last-10-simulation)
        - [5. CSV Export with Moodle Database (Last 10, Simulation)](#5-csv-export-with-moodle-database-last-10-simulation)
  - [Operation](#operation)
    - [Script Output](#script-output)
    - [Administration Interface](#administration-interface)
      - [Recorder:](#recorder)
      - [List of Recordings:](#list-of-recordings)
      - [Import of External Videos:](#import-of-external-videos)
    - [Logs of the Solution](#logs-of-the-solution)
      - [Asynchronous Tasks (CELERY\_TO\_ENCODE = True)](#asynchronous-tasks-celery_to_encode--true)
      - [RabbitMQ-Server](#rabbitmq-server)
      - [bbb-recorder](#bbb-recorder)
      - [Deletion of External Recordings from the Video Import Module](#deletion-of-external-recordings-from-the-video-import-module)

# BigBlueButton Infrastructure Migration, with Pod Support

## Context

As part of the recovery plan, a virtual classroom solution from the Ministry of Higher Education and Research (ESR), based on the free and open-source software BigBlueButton (BBB), has been deployed nationwide.

More information can be found on the following websites:

- [ESR Digital Documentation](https://doc.numerique-esr.fr/)
- [Virtual Classrooms and Webinars for Higher Education](https://www.enseignementsup-recherche.gouv.fr/fr/classes-virtuelles-et-webinaires-pour-l-enseignement-superieur-90257)

For institutions that have never had a local BigBlueButton infrastructure, using this virtual classroom solution (BBB ESR) is straightforward.

However, for institutions that previously had a local BBB infrastructure, using the ESR's BBB has impacts for users. This documentation can be useful for these institutions.

## Impacts

Changing infrastructure is extremely simple, regardless of the platform:

- **Pod**: Change the configuration of the Meetings module in the `custom/settings_local.py` file, specifically `BBB_API_URL` and `BBB_SECRET_KEY`.
- **Moodle (v4)**: Change the configuration, accessible via the Site Administration module, specifically the BigBlueButton server URL and the BigBlueButton shared secret.
- **Greenlight**: Change the configuration in the `.env` file, specifically `BIGBLUEBUTTON_ENDPOINT` and `BIGBLUEBUTTON_SECRET`.

By modifying these parameters, the platform will point to the new BBB architecture.

For users, the impacts concern recordings, which will no longer be visible. Sessions/meetings will still be accessible to users, as they are saved on the respective platform, but not the recordings. These recordings are saved directly on the BBB infrastructure (either on the BBB server or the Scalelite server). In the platforms, links to these recordings are displayed when viewing the session/meeting.

Ultimately, when changing infrastructure, old recordings will no longer be displayed to users; and when the old BBB architecture is shut down, old recordings will no longer be available if nothing has been done beforehand.

## Constraints

Here is a reminder of the constraints to consider, which explain the proposed solution:

- **Constraint regarding Pod**: We no longer wish to use the old BBB module of Pod, which will soon disappear.
- **Constraint of the BBB API**: Participants and moderators are only available when the BBB session is in progress. Once stopped, the information is no longer in BBB. We only have this information in the BBB client, i.e., Pod or Moodle (or Greenlight...).
- **BBB Constraint**: By default, it is possible to reconstruct a BBB recording (typically to get the recording in video format) only if the raw files are still present. By default, these raw files are deleted after 14 days. Therefore, the solution cannot be based on reconstructing recordings.

## Provided Solution

The idea is based on:

- The recording claim system of Pod (see [ESUP-Portail Documentation](https://www.esup-portail.org/wiki/x/DgB8Lw)).
- The external video import system to add the possibility of converting BBB recordings, presentation type, into video (via the `bbb-recorder` plugin, see below).
- A migration script, which offers several possibilities.

This solution relies entirely on Pod and does not impact BigBlueButton in any way. No modifications are required on the BigBlueButton side.
{: .alert .alert-info}

This migration script is configurable and offers several possibilities:

1. **For those with few recordings to recover**:
   - This script will convert presentations from the old BBB architecture into video files (via the `bbb-recorder` plugin) and place these files in the directory for Recording Claim.
   - Of course, if there are already video presentations, the video file will be directly copied.
   - Once all videos have been encoded, the local BBB architecture can be shut down. Users will need to retrieve their videos from the Recording Claim tab in Pod.

2. **For those with many recordings to recover**:
   - The idea is to give users time to choose which recordings they want to keep (it is not possible or useful to convert everything).
   - For this, the old BBB/Scalelite server must remain open for at least a few months (just to access the recordings).
   - On the script side, if necessary, access to the Moodle database will be required to know who did what.
   - Thus, for each BBB recording, the script will create a line in "My External Videos," of type BigBlueButton, for the moderators (who will be created if necessary in the Pod database). They can then import these recordings into Pod themselves.
   - In case some recordings are not identifiable, they will be associated with an administrator (to be configured in the script).
   - Additionally, if access to the Moodle database allows, an informational message will be placed directly in Moodle, at the level of the concerned BBB sessions.

![BigBlueButton Infrastructure Migration](bbb-infrastructure-migration_screens/external_videos.png)

The script is designed to be configurable, with the ability to manage a certain number of recordings and to test it beforehand (using a dry mode).

# Architecture of the Solution

## Plugin `bbb-recorder`

To convert BBB playback presentations, I based it on the GitHub project `bbb-recorder`: a plugin, independent of BigBlueButton, that allows converting - via a script - a BigBlueButton web presentation into a video file.

If needed, this plugin also allows live streaming (RTMP stream) of a BigBlueButton course.

This plugin `bbb-recorder` had already been used for the old system, in Pod v2 (see [ESUP-Portail Documentation](https://www.esup-portail.org/wiki/x/AgCBNg)) and has been used successfully many times.

### Functioning of `bbb-recorder`

Running the `bbb-recorder` script performs the following steps:

1. Launches a Chrome browser in the background.
2. Chrome visits the provided link corresponding to the BigBlueButton web presentation.
3. It performs screen recording in the form of a video file.

### Installation of `bbb-recorder` on Encoding Servers

The reference documentation is accessible [here](https://github.com/jibon57/bbb-recorder).

For my part, on Debian 11 servers, here is what was done.

#### Installation of Chrome and Prerequisites

```bash
sudo -i
apt install xvfb
curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get -y update
apt-get -y install google-chrome-stable
```

(info) Being an encoding server, I assume that `ffmpeg` is already installed. If necessary, `ffmpeg` must be installed.

#### Effective Installation

Here is the installation for a `pod` user.

```bash
cd ~
git clone https://github.com/jibon57/bbb-recorder
cd bbb-recorder
npm install --ignore-scripts
cp .env.example .env
```

Management of the directory containing the videos: in my case `/data/www/pod/bbb-recorder` and the log directory `/data/www/pod/bbb-recorder/logs`.

```bash
mkdir /data/www/pod/bbb-recorder
mkdir /data/www/pod/bbb-recorder/logs
```

If `bbb-recorder` was not installed with the correct user (`pod`), the generated video files may not be accessible by the Pod user and thus may not be encoded by the encoding servers.

In practice, this results in a 1° successful encoding: the BBB web presentation will be converted into a video file, but this video file will not be accessible to Pod and cannot be converted into a Pod video.

### Configuration of `bbb-recorder`

- Edit the configuration file `~/bbb-recorder/.env` to configure the RTMP (not useful here) and especially the video directory.

```json
{
  "rtmpUrl": "rtmp://xxxxxxxx:xxxxxxxxxx@xxxxx.univ.fr:1935/live/stream",
  "ffmpegServer": "ws://localhost",
  "ffmpegServerPort": 4000,
  "auth": "xxxx",
  "copyToPath": "/data/www/pod/bbb-recorder"
}
```

- If needed, configure in the `examples/index.js` file (for live streaming or direct recording of a web conference):

```javascript
const BBBUrl = "https://xxxx.univ.fr/bigbluebutton/";
BBBSalt = "xxxxxxxxxxxxxxxxxxxx";
joinName = "recorder";
```

- If you wish, you can configure the bitrate to control the quality of the exported video by adjusting the `videoBitsPerSecond` property in `background.js`.

Note that `bbb-recorder` uses a temporary directory to generate a video before it is copied to the configured directory (see `copyToPath`). This temporary directory corresponds to `../Downloads`.

Thus, in the case of an installation in the home directory of the `pod` user, the temporary directory created and used by `bbb-recorder` is `/home/pod/Downloads`.

It is necessary to ensure sufficient storage space is available.

## Configuration

### Configuration in Pod

Once `bbb-recorder` is installed on the various encoding servers, the `bbb` plugin must be configured directly in Pod, by editing the `custom/settings_local.py` file (on the encoders and on the frontend):

```python
# Use import-video module
USE_IMPORT_VIDEO = True

# Use plugin bbb-recorder for import-video module
# Useful to convert presentation playback to video file
USE_IMPORT_VIDEO_BBB_RECORDER = True

# Directory of bbb-recorder plugin (see documentation https://github.com/jibon57/bbb-recorder)
# bbb-recorder must be installed in this directory, on all encoding servers
# bbb-recorder create a directory Downloads, at the same level, that needs disk space
IMPORT_VIDEO_BBB_RECORDER_PLUGIN = '/home/pod/bbb-recorder/'

# Directory that will contain the video files generated by bbb-recorder
IMPORT_VIDEO_BBB_RECORDER_PATH = '/data/www/pod/bbb-recorder/'
```

The configuration elements are as follows:

- `USE_IMPORT_VIDEO`: Use (True/False) of the video import module for Pod.
- `USE_IMPORT_VIDEO_BBB_RECORDER`: Use (True/False) of the `bbb-recorder` plugin for the video import module; useful for converting a BigBlueButton presentation into a video file.
- `IMPORT_VIDEO_BBB_RECORDER_PLUGIN`: Directory of the `bbb-recorder` plugin (see [bbb-recorder documentation](https://github.com/jibon57/bbb-recorder)). `bbb-recorder` must be installed in this directory on all encoding servers. `bbb-recorder` creates a `Downloads` directory at the same level, which requires disk space.
- `IMPORT_VIDEO_BBB_RECORDER_PATH`: Directory that will contain the video files generated by `bbb-recorder`.

If you use the 1° option of the script, i.e., the recording claim system, you can choose not to give users the functionality to convert BBB presentations into video files. Thus, you can set `USE_IMPORT_VIDEO_BBB_RECORDER = False` in this case.

The other parameters are necessary, at a minimum, when executing the script.

Regarding the directory containing the video files generated by `bbb-recorder` (`IMPORT_VIDEO_BBB_RECORDER_PATH`), it must be created manually - along with its log subdirectory - with the following command lines; feel free to modify them according to your system architecture and permissions:

```bash
mkdir /data/www/pod/bbb-recorder/logs -p
chown pod:nginx /data/www/pod/bbb-recorder/logs
```

While automatic creation of these directories would have been possible, considering the potential issues related to architecture and permissions, it seemed preferable for the Pod administrator to create these two directories manually. They know what they are doing and can choose the location, permissions, or other aspects.

### Script `migrate_bbb_recordings`

This script is accessible in Pod, in the `pod/video/management/commands/migrate_bbb_recordings` directory.

This script cannot be executed as is; it is essential to perform additional configuration, independent of the Pod configuration, directly in this file.

If you have a large number of recordings on an old version of BBB (tested in 2.2), you may encounter a 404 error when executing the script, related to the nginx timeout on the BBB server. In this case, you will need to increase its value in the `/etc/bigbluebutton/nginx/web.nginx` file of the BBB server.

See [github.com/bigbluebutton/bigbluebutton/issues/10570](https://github.com/bigbluebutton/bigbluebutton/issues/10570)

#### Script Functioning

As mentioned above, this script offers 2 possibilities:

1. **For those with few recordings to recover**:
   - This script will convert presentations from the old BBB architecture into video files (via the `bbb-recorder` plugin) and place these files in the directory of a recorder for Recording Claim (see [ESUP-Portail Documentation](https://www.esup-portail.org/wiki/x/DgB8Lw)).
   - Of course, if there are already video presentations, the video file will be directly copied.
   - Once all videos have been encoded, the local BBB architecture can be shut down. Users will need to retrieve their videos from the Recording Claim tab in Pod.
   - This is possible using the `--use-manual-claim` parameter and the configuration directly in this file.
   - Please note that depending on your Pod architecture, encoding will be performed either via Celery tasks or directly, one after the other.
   - Feel free to test with a few recordings and run this script in the background (using `&`).

2. **For those with many recordings to recover**:
   - The idea is to give users time to choose which recordings they want to keep (it is not possible or useful to convert everything).
   - For this, the old BBB/Scalelite server must remain open for at least a few months (just to access the recordings).
   - On the script side, if necessary, access to the Moodle database will be required to know who did what.
   - Thus, for each BBB recording, the script will create a line in "My External Videos," of type BigBlueButton, for the moderators (who will be created if necessary in the Pod database). They can then import these recordings into Pod themselves. If some recordings are not identifiable (for example, from sources other than Pod or Moodle), they will be associated with an administrator (to be configured in the script).
   - Additionally, if access to the Moodle database allows, an informational message will be placed directly in Moodle, at the level of the concerned BBB sessions.
   - This is possible using the `--use-import-video` parameter, the optional `--use-database-moodle` parameter, and the configuration directly in this file.

3. **You can also perform a CSV export of the list of BBB recordings** (allowing you to process them elsewhere).
   - This is possible using the `--use-export-csv` parameter, the optional `--use-database-moodle` parameter, and the configuration directly in this file.

This script also allows you to:

- Simulate what will be done using the `--dry` parameter.
- Process only certain lines using the `--min-value-record-process` and `--max-value-record-process` parameters.

This script has been tested with Moodle 4.

#### Internal Script Configuration

| Parameter                  | Description                                                                                                                                                       | Default Value / Format                                                                                                                                              |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `SCRIPT_BBB_SERVER_URL`   | Old URL of the BigBlueButton/Scalelite server                                                                                                                  | `'https://bbb.univ.fr/'`                                                                                                                                                |
| `SCRIPT_BBB_SECRET_KEY`   | BigBlueButton or Scalelite `LOADBALANCER_SECRET` key                                                                                                              | `'xxxxxxxxxx'`                                                                                                                                                          |
| `SCRIPT_PLAYBACK_URL_23`  | Is the BBB version greater than 2.3, regarding playback URLs? Useful for reading presentations in 2.0 format (<=2.2) or 2.3 format (>=2.3)                         | `True`                                                                                                                                                                  |
| `SCRIPT_RECORDER_ID`      | Recorder used to retrieve BBB recordings (useful with `--use-manual-claim`)                                                                                      | `1`                                                                                                                                                                     |
| `SCRIPT_ADMIN_ID`         | Administrator to whom the recordings will be added if the moderators are not identified (useful with `--use-import-video`)                                        | `1`                                                                                                                                                                     |
| `DB_PARAMS`               | Moodle database connection parameters (useful with `--use-import-video` and `--use-database-moodle`)                                                             | See details below                                                                                                                                                 |
| `SCRIPT_INFORM`           | Informational message that will be set in Moodle (`mdl_bigbluebuttonbn.intro`)                                                                                   | *Preliminary message for the University of Montpellier*                                                                                                                 |
| `IGNORED_SERVERS`         | List of servers to ignore                                                                                                                                       | `["not-a-moodle.univ.fr"]`                                                                                                                                              |
| `USE_CACHE`               | Use the last BBB response stored in an XML file instead of re-running the request                                                                              | `False`                                                                                                                                                                 |
{: .table .table-striped}

#### Format of `DB_PARAMS`

```json
{
    "default": {
        "host": "bddmoodle.univ.fr",
        "database": "moodle",
        "user": "moodle",
        "password": "",
        "port": null,
        "connect_timeout": 10
    },
    "server2": {
        "host": "bddmoodle.univ.fr",
        "database": "moodle2",
        "user": "moodle2",
        "password": "",
        "port": null,
        "connect_timeout": 10
    }
}
```

#### Script Arguments

| Argument                     | Description                                                                                                                            | Default Value / Format |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------|----------------------------|
| `--use-manual-claim`        | Use manual claim                                                                                                                       | `False`                    |
| `--use-import-video`        | Use video import module                                                                                                                 | `False`                    |
| `--use-database-moodle`     | Use Moodle database to search for moderators (requires `--use-import-video` or `--use-export-csv`)                                    | `False`                    |
| `--min-value-record-process`| Minimum value of recordings to process                                                                                                  | `1`                        |
| `--max-value-record-process`| Maximum value of recordings to process                                                                                                  | `10000`                    |
| `--dry`                     | Simulate what will be done                                                                                                             | `False`                    |
| `--use-export-csv`          | Export recordings to CSV format (with `--use-database-moodle` to include moderators)                                                  | `False`                    |
{: .table .table-striped}

#### Examples and Use Cases

⚠️ Before executing this script without simulation, **remember to perform the necessary backups** (Pod database, Moodle database if write access is required).

##### Initialization

```bash
cd /usr/local/django_projects/podv3
workon django_pod3
```

##### 1. Claiming All Recordings (Simulation)

```bash
python -W ignore manage.py migrate_bbb_recordings --use-manual-claim --dry
```

##### 2. Claiming the Last 2 Recordings (Simulation)

```bash
python -W ignore manage.py migrate_bbb_recordings --min-value-record-process=1 --max-value-record-process=2 --use-manual-claim --dry &
```

##### 3. External Video Import with Moodle Database (Simulation)

```bash
python -W ignore manage.py migrate_bbb_recordings --use-import-video --use-database-moodle --dry
```

##### 4. External Video Import without Moodle Database (Last 10, Simulation)

```bash
python -W ignore manage.py migrate_bbb_recordings --min-value-record-process=1 --max-value-record-process=10 --use-import-video --dry
```

##### 5. CSV Export with Moodle Database (Last 10, Simulation)

```bash
python3 manage.py migrate_bbb_recordings --use_export_csv --use-database-moodle --max-value-record-process=10 --dry
```

## Operation

### Script Output

The script displays a set of information for each processed line; do not hesitate to run it in dry mode.
![Script](bbb-infrastructure-migration_screens/script.png)

> 💡 It is possible to run the script multiple times; this will not create duplicates. However, it may re-encode recordings that were already encoded during the first pass.

### Administration Interface

#### Recorder:

![Recorder](bbb-infrastructure-migration_screens/administration_recorder.png)

#### List of Recordings:

![List](bbb-infrastructure-migration_screens/administration_recordings.png)

#### Import of External Videos:

![Import](bbb-infrastructure-migration_screens/administration_import.png)

### Logs of the Solution

Depending on your environment, Pod logs can be found in the `/var/log/syslog` file.

#### Asynchronous Tasks (CELERY_TO_ENCODE = True)

On encoding servers, Celery logs are located in **/var/log/celery/worker1.log** (depending on your configuration, if you use multiple workers, you may have multiple files).

#### RabbitMQ-Server

If you use RabbitMQ-Server, on this server, you can find information in **/var/log/rabbitmq/rabbit@xxxxx.log**.

#### bbb-recorder

The logs of `bbb-recorder` processes are accessible in the directory configured via **IMPORT_VIDEO_BBB_RECORDER_PATH/logs**.

#### Deletion of External Recordings from the Video Import Module

If you opted for the 2° possibility and the use of the video import module: on the day of the **complete shutdown of your old infrastructure**, the old links will no longer work.
If you wish to delete the external recordings that concerned your old infrastructure, you can do so directly via an SQL query to be executed in the Pod database, namely:

```sql
# Replace SCRIPT_BBB_SERVER_URL with the correct value, according to your environment
DELETE FROM import_video_externalrecording WHERE source_url like 'SCRIPT_BBB_SERVER_URL%'
```

> 💡 I prefer not to include this query in the script; it is up to you to decide when you want to perform this deletion. Of course, don't forget to make a backup first.
