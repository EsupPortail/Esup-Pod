# 

## General information

* `CAS`
  > default value: `1.5.3`
* `ModelTranslation`
  > default value: `0.19.11`
* `captcha`
  > default value: `0.6.0`
* `chunked_upload`
  > default value: `2.0.0`
* `ckeditor`
  > default value: `6.3.0`
  >> WARNING (ckeditor.W001) django-ckeditor bundles CKEditor 4.22.1 free version<br>
  >> which isn’t supported anmyore and which does have unfixed security issues,<br>
  >> see for example https://ckeditor.com/cke4/release/CKEditor-4.24.0-LTS .<br>
  >> You should consider strongly switching to a different editor.<br>
* `django_select2`
  > default value: `latest`
* `honeypot`
  > default value: `1.2.1`
* `mozilla_django_oidc`
  > default value: `4.0.1`
* `pwa`
  > default value: `2.0.1`
* `rest_framework`
  > default value: `3.15.2`
* `shibboleth`
  > default value: `latest`
* `sorl.thumbnail`
  > default value: `12.11.0`
* `tagging`
  > default value: `0.5.0`
* `tagulous`
  > default value: `2.1.0`
  >> Managing keywords associated with a Django object.<br>
  >> [django-tagulous.readthedocs.io](https://django-tagulous.readthedocs.io)<br>

## 

### Database

* `DATABASES`
  > default value:

  ```python
  {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
      }
  }
  ```

  >>

### Email

* `CONTACT_US_EMAIL`
  > default value: ``
  >>
* `CUSTOM_CONTACT_US`
  > default value: `False`
  >>
* `DEFAULT_FROM_EMAIL`
  > default value: `noreply`
  >>
* `EMAIL_HOST`
  > default value: `smtp.univ.fr`
  >>
* `EMAIL_PORT`
  > default value: `25`
  >>
* `EMAIL_SUBJECT_PREFIX`
  > default value: ``
  >>
* `NOTIFY_SENDER`
  > default value: `True`
  >> In unauthenticated mode, when using the contact form, sends a copy of the message to the address entered in the form.<br>
* `SERVER_EMAIL`
  > default value: `noreply`
  >>
* `SUBJECT_CHOICES`
  > default value: `()`
  >>
* `SUPPORT_EMAIL`
  > default value: `None`
  >>
* `USER_CONTACT_EMAIL_CASE`
  > default value: ``
  >>
* `USE_ESTABLISHMENT_FIELD`
  > default value: `False`
  >>

### Encoding

* `FFMPEG_AUDIO_BITRATE`
  > default value: `192k`
  >>
* `FFMPEG_CMD`
  > default value: `ffmpeg`
  >>
* `FFMPEG_CREATE_THUMBNAIL`
  > default value: `-vf "fps=1/(%(duration)s/%(nb_thumbnail)s)" -vsync vfr "%(output)s_%%04d.png"`
  >>
* `FFMPEG_CRF`
  > default value: `20`
  >>
* `FFMPEG_EXTRACT_SUBTITLE`
  > default value: `-map 0:%(index)s -f webvtt -y "%(output)s"`
  >>
* `FFMPEG_EXTRACT_THUMBNAIL`
  > default value: `-map 0:%(index)s -an -c:v copy -y "%(output)s"`
  >>
* `FFMPEG_HLS_COMMON_PARAMS`
  > default value: `-c:v %(libx)s -preset %(preset)s -profile:v %(profile)s -pix_fmt yuv420p -level %(level)s -crf %(crf)s -sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -c:a aac -ar 48000 -max_muxing_queue_size 4000`
  >>
* `FFMPEG_HLS_ENCODE_PARAMS`
  > default value: `-vf "scale=-2:%(height)s" -maxrate %(maxrate)s -bufsize %(bufsize)s -b:a:0 %(ba)s -hls_playlist_type vod -hls_time %(hls_time)s -hls_flags single_file -master_pl_name "livestream%(height)s.m3u8" -y "%(output)s"`
  >>
* `FFMPEG_HLS_TIME`
  > default value: `2`
  >>
* `FFMPEG_INPUT`
  > default value: `-hide_banner -threads %(nb_threads)s -i "%(input)s"`
  >>
* `FFMPEG_LEVEL`
  > default value: `3`
  >>
* `FFMPEG_LIBX`
  > default value: `libx264`
  >>
* `FFMPEG_M4A_ENCODE`
  > default value: `-vn -c:a aac -b:a %(audio_bitrate)s "%(output)s"`
  >>
* `FFMPEG_MP3_ENCODE`
  > default value: `-vn -codec:a libmp3lame -qscale:a 2 -y "%(output)s"`
  >>
* `FFMPEG_MP4_ENCODE`
  > default value: `-map 0:v:0 %(map_audio)s -c:v %(libx)s -vf "scale=-2:%(height)s" -preset %(preset)s -profile:v %(profile)s -pix_fmt yuv420p -level %(level)s -crf %(crf)s -maxrate %(maxrate)s -bufsize %(bufsize)s -sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -c:a aac -ar 48000 -b:a %(ba)s -movflags faststart -y -vsync 0 "%(output)s"`
  >>
* `FFMPEG_NB_THREADS`
  > default value: `0`
  >>
* `FFMPEG_NB_THUMBNAIL`
  > default value: `3`
  >>
* `FFMPEG_PRESET`
  > default value: `slow`
  >>
* `FFMPEG_PROFILE`
  > default value: `high`
  >>
* `FFMPEG_STUDIO_COMMAND`
  > default value: `-hide_banner -threads %(nb_threads)s %(input)s %(subtime)s -c:a aac -ar 48000 -c:v h264 -profile:v high -pix_fmt yuv420p -crf %(crf)s -sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -deinterlace`
  >>
* `FFPROBE_CMD`
  > default value: `ffprobe`
  >>
* `FFPROBE_GET_INFO`
  > default value: `%(ffprobe)s -v quiet -show_format -show_streams %(select_streams)s -print_format json -i %(source)s`
  >>
* `FFMPEG_DRESSING_OUTPUT`
  > default value: ` -c:v libx264 -y -vsync 0 %(output)s `
  >> Specifies the FFmpeg output encoding settings for generating the temporary dressed video file, using the H.264 codec with forced overwrite and synchronized video output.<br>
* `FFMPEG_DRESSING_INPUT`
  > default value: ` -i %(input)s `
  >> Defines the input file for FFmpeg processing of the intermediate dressed video.<br>
* `FFMPEG_DRESSING_FILTER_COMPLEX`
  > default value: ` -filter_complex %(filter)s `
  >> Applies complex filter chains to the intermediate dressed video using FFmpeg.<br>
* `FFMPEG_DRESSING_WATERMARK`
  > default value: ` [1]format=rgba,colorchannelmixer=aa=%(opacity)s[logo]; [logo][vid]scale2ref=oh*mdar:ih*0.1[logo][video2]; [video2][logo]%(position)s%(name_out)s `
  >> Adds a watermark to the intermediate dressed video with customizable opacity and position.<br>
* `FFMPEG_DRESSING_SCALE`
  > default value: `[%(number)s]scale=w='if(gt(a,16/9),16/9*%(height)s,-2)':h='if(gt(a,16/9),-2,%(height)s)',pad=ceil(16/9*%(height)s):%(height)s:(ow-iw)/2:(oh-ih)/2[%(name)s]`
  >> Rescales the intermediate dressed video to maintain a 16:9 aspect ratio with padding if necessary.<br>
* `FFMPEG_DRESSING_CONCAT`
  > default value: `%(params)sconcat=n=%(number)s:v=1:a=1:unsafe=1[v][a]`
  >> Concatenates multiple video and audio streams into a single temporary dressed video output.<br>
* `FFMPEG_DRESSING_SILENT`
  > default value: ` -f lavfi -t %(duration)s -i anullsrc=r=44100:cl=stereo`
  >> Generates silent audio of specified duration for the temporary dressed video.<br>
* `FFMPEG_DRESSING_AUDIO`
  > default value: `[%(param_in)s]anull[%(param_out)s]`
  >> Processes audio without modifications for inclusion in the temporary dressed video.<br>

### file management

* `FILES_DIR`
  > default value: `files`
  >>
* `FILE_UPLOAD_TEMP_DIR`
  > default value: `/var/tmp`
  >>
* `MEDIA_ROOT`
  > default value: `/pod/media`
  >>
* `MEDIA_URL`
  > default value: `/media/`
  >>
* `STATICFILES_STORAGE`
  > default value: ``
  >>
* `STATIC_ROOT`
  > default value: `/pod/static`
  >>
* `STATIC_URL`
  > default value: `/static/`
  >>
* `USE_PODFILE`
  > default value: `False`
  >>
* `VIDEOS_DIR`
  > default value: `videos`
  >>

### language



* `LANGUAGES`
  > default value: `(('fr', 'Français'), ('en', 'English')))`
  >>
* `LANGUAGE_CODE`
  > default value: `fr`
  >>

### Main

* `ADMINS`
  > default value: `[("Name", "adminmail@univ.fr"),]`
  >>
* `ALLOWED_HOSTS`
  > default value: `['pod.localhost']`
  >>
* `BASE_DIR`
  > default value: `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`
  >>
* `CACHES`
  > default value: `{}`
  >>
* `CSRF_COOKIE_SECURE`
  > default value: `not DEBUG`
  >>
* `DEBUG`
  > default value: `True`
  >>
* `USE_DEBUG_TOOLBAR`
  > default value: `True`
  >> A boolean value that enables or disables the debugging tool.<br><br>
  >> Never deploy a production site with USE_DEBUG_TOOLBAR enabled.<br><br>
  >> _ref : [django-debug-toolbar.readthedocs.io](https://django-debug-toolbar.readthedocs.io/en/latest/)_<br>
* `LOGIN_URL`
  > default value: `/authentication_login/`
  >>
* `MANAGERS`
  > default value: `[]`
  >>
* `PROXY_HOST`
  > default value: ``
  >>
* `PROXY_PORT`
  > default value: ``
  >>
* `SECRET_KEY`
  > default value: `A_CHANGER`
  >>
* `SECURE_SSL_REDIRECT`
  > default value: `False`
  >> Unless your site should be available over both SSL and non-SSL<br>
  >> connections, you may want to either set this setting True<br>
  >> or configure a load balancer or reverse-proxy server<br>
  >> to redirect all connections to HTTPS.<br>
* `SESSION_COOKIE_AGE`
  > default value: `14400`
  >>
* `SESSION_COOKIE_SAMESITE`
  > default value: `Lax`
  >>
* `SESSION_COOKIE_SECURE`
  > default value: `not DEBUG`
  >>
* `SESSION_EXPIRE_AT_BROWSER_CLOSE`
  > default value: `True`
  >>
* `SITE_ID`
  > default value: `1`
  >>
* `TEST_SETTINGS`
  > default value: `False`
  >> Use to check if globals settings are in test mode or not.<br>
* `THIRD_PARTY_APPS`
  > default value: `[]`
  >>
* `TIME_ZONE`
  > default value: `UTC`
  >>

### Obsolescence

* `ACCOMMODATION_YEARS`
  > default value: `{}`
  >>
* `ARCHIVE_OWNER_USERNAME`
  > default value: `"archive"`
  >>
* `ARCHIVE_HOW_MANY_DAYS`
  > default value: `365`
  >> Delay before an archived video is moved to archive_ROOT.<br>
* `POD_ARCHIVE_AFFILIATION`
  > default value: `[]`
  >>
* `WARN_DEADLINES`
  > default value: `[60, 30, 7]`
  >>

### Templating

* `COOKIE_LEARN_MORE`
  > default value: ``
  >>
* `DARKMODE_ENABLED`
  > default value: `True`
  >> Allows users to enable a dark mode.<br>
* `DYSLEXIAMODE_ENABLED`
  > default value: `True`
  >> Allows to use a font that is more suitable for people with dyslexia.<br>
* `HIDE_CHANNEL_TAB`
  > default value: `False`
  >>
* `HIDE_CURSUS`
  > default value: `False`
  >>
* `HIDE_DISCIPLINES`
  > default value: `False`
  >>
* `HIDE_LANGUAGE_SELECTOR`
  > default value: `False`
  >>
* `HIDE_SHARE`
  > default value: `False`
  >>
* `HIDE_TAGS`
  > default value: `False`
  >>
* `HIDE_TYPES`
  > default value: `False`
  >>
* `HIDE_TYPES_TAB`
  > default value: `False`
  >>
* `HIDE_USERNAME`
  > default value: `False`
  >>
* `HIDE_USER_FILTER`
  > default value: `False`
  >>
* `HIDE_USER_TAB`
  > default value: `False`
  >>
* `HOMEPAGE_NB_VIDEOS`
  > default value: `12`
  >>
* `HOMEPAGE_SHOWS_PASSWORDED`
  > default value: `False`
  >>
* `HOMEPAGE_SHOWS_RESTRICTED`
  > default value: `False`
  >>
* `MENUBAR_HIDE_INACTIVE_OWNERS`
  > default value: `True`
  >>
* `MENUBAR_SHOW_STAFF_OWNERS_ONLY`
  > default value: `False`
  >>
* `SHIB_NAME`
  > default value: `Identify Federation`
  >>
* `SHOW_EVENTS_ON_HOMEPAGE`
  > default value: `False`
  >>
* `SHOW_ONLY_PARENT_THEMES`
  > default value: `False`
  >>
* `TEMPLATE_VISIBLE_SETTINGS`
  > default value: `{}`
  >>

### Transcoding

* `TRANSCRIPTION_AUDIO_SPLIT_TIME`
  > default value: `600`
  >>
* `TRANSCRIPTION_MODEL_PARAM`
  > default value: `{}`
  >>
* `TRANSCRIPTION_NORMALIZE`
  > default value: `False`
  >>
* `TRANSCRIPTION_NORMALIZE_TARGET_LEVEL`
  > default value: `-16.0`
  >>
* `TRANSCRIPTION_STT_SENTENCE_BLANK_SPLIT_TIME`
  > default value: `0.5`
  >> Maximum time in seconds of gaps between each word for cutting subtitles with the STT tool.<br>
* `TRANSCRIPTION_STT_SENTENCE_MAX_LENGTH`
  > default value: `2`
  >> Maximum time in seconds for a sentence when transcribing with the STT tool.<br>
* `TRANSCRIPTION_TYPE`
  > default value: `STT`
  >>
* `TRANSCRIPT_VIDEO`
  > default value: `start_transcript`
  >>
* `USE_TRANSCRIPTION`
  > default value: `False`
  >>

## 

### AI Enhancement application configuration

AI Enhancement app to be able to use artificial intelligence enhancements for videos.<br>
Set `USE_AI_ENHANCEMENT` to True to activate this application.<br>

* `AI_ENHANCEMENT_API_URL`
  > default value: ``
  >> API URL for the AI video enhancement.<br>
  >> Example: 'https://aristote.univ.fr/api'<br>
  >> Project Link: https://www.demainestingenieurs.centralesupelec.fr/aristote/<br>
* `AI_ENHANCEMENT_API_VERSION`
  > default value: ``
  >> API version for the AI video enhancement.<br>
* `AI_ENHANCEMENT_CGU_URL`
  > default value: ``
  >> URL for General Terms and Conditions for API uses for the AI video enhancement.<br>
  >> Example: '<https://aristote.univ.fr/cgu>'<br>
  >> Project Link: <https://www.demainestingenieurs.centralesupelec.fr/aristote/><br>
* `AI_ENHANCEMENT_CLIENT_ID`
  > default value: `mocked_id`
  >> The video enhancement AI client ID.<br>
  >> Example: 'v1'<br>
* `AI_ENHANCEMENT_CLIENT_SECRET`
  > default value: `mocked_secret`
  >> The video enhancement AI client secret password.<br>
* `AI_ENHANCEMENT_FIELDS_HELP_TEXT`
  > default value: ``
  >> Set of help texts displayed with the form for improving a video with Aristotle's AI.<br>
* `USE_AI_ENHANCEMENT`
  > default value: `False`
  >> Activation of artificial intelligence enhancements. Allows users to use it.<br>
* `AI_ENHANCEMENT_PROXY_URL`
  > default value: ``
  >> URL of proxy server for request coming from Aristote.<br>
  >> Exemple : '<https://proxy_aristote.univ.fr>'<br>

### 

* `AFFILIATION`
  > default value: ``
  >>
* `AFFILIATION_EVENT`
  > default value: ``
  >>
* `AFFILIATION_STAFF`
  > default value: ``
  >>
* `AUTH_CAS_USER_SEARCH`
  > default value: `user`
  >>
* `AUTH_LDAP_BIND_DN`
  > default value: ``
  >>
* `AUTH_LDAP_BIND_PASSWORD`
  > default value: ``
  >>
* `AUTH_LDAP_USER_SEARCH`
  > default value: ``
  >>
* `AUTH_TYPE`
  > default value: ``
  >>
* `CAS_ADMIN_AUTH`
  > default value: `False`
  >> To disable CAS authentication for the entire django admin app, set CAS_ADMIN_AUTH = False<br>
* `CAS_FORCE_LOWERCASE_USERNAME`
  > default value: `False`
  >>
* `CAS_GATEWAY`
  > default value: `False`
  >>
* `CAS_LOGOUT_COMPLETELY`
  > default value: `True`
  >> See [kstateome/django-cas](https://github.com/kstateome/django-cas)<br>
* `CAS_SERVER_URL`
  > default value: `sso_cas`
  >>
* `CREATE_GROUP_FROM_AFFILIATION`
  > default value: `False`
  >>
* `CREATE_GROUP_FROM_GROUPS`
  > default value: `False`
  >>
* `DEFAULT_AFFILIATION`
  > default value: ``
  >>
* `ESTABLISHMENTS`
  > default value: ``
  >>
* `GROUP_STAFF`
  > default value: `AFFILIATION_STAFF`
  >>
* `HIDE_LOCAL_LOGIN`
  > default value: `False`
  >>
* `HIDE_USERNAME`
  > default value: `False`
  >>
* `LDAP`
  > default value: ``
  >>
* `LDAP_SERVER`
  > default value: ``
  >>
* `OIDC_CLAIM_FAMILY_NAME`
  > default value: `family_name`
  >>
* `OIDC_CLAIM_PREFERRED_USERNAME`
  > default value: `preferred_username`
  >>
* `OIDC_CLAIM_GIVEN_NAME`
  > default value: `given_name`
  >>
* `OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES`
  > default value: `[]`
  >>
* `OIDC_DEFAULT_AFFILIATION`
  > default value: ``
  >>
* `OIDC_NAME`
  > default value: ``
  >>
* `OIDC_OP_AUTHORIZATION_ENDPOINT`
  > default value: `https`
  >>
* `OIDC_OP_JWKS_ENDPOINT`
  > default value: `https`
  >>
* `OIDC_OP_TOKEN_ENDPOINT`
  > default value: `https`
  >>
* `OIDC_OP_USER_ENDPOINT`
  > default value: `https`
  >>
* `OIDC_RP_CLIENT_ID`
  > default value: `os.environ`
  >>
* `OIDC_RP_CLIENT_SECRET`
  > default value: `os.environ`
  >>
* `OIDC_RP_SIGN_ALGO`
  > default value: ``
  >>
* `POPULATE_USER`
  > default value: `None`
  >>
* `REMOTE_USER_HEADER`
  > default value: `REMOTE_USER`
  >>
* `SHIBBOLETH_ATTRIBUTE_MAP`
  > default value: ``
  >>
* `SHIBBOLETH_STAFF_ALLOWED_DOMAINS`
  > default value: ``
  >>
* `SHIB_LOGOUT_URL`
  > default value: ``
  >>
* `SHIB_NAME`
  > default value: ``
  >>
* `SHIB_URL`
  > default value: ``
  >>
* `USER_CAS_MAPPING_ATTRIBUTES`
  > default value: ``
  >>
* `USER_LDAP_MAPPING_ATTRIBUTES`
  > default value: ``
  >>
* `USE_CAS`
  > default value: `False`
  >>
* `USE_OIDC`
  > default value: `False`
  >>
* `USE_SHIB`
  > default value: `False`
  >>

### 


### 

* `ACTIVE_MODEL_ENRICH`
  > default value: `False`
  >>
* `ALL_LANG_CHOICES`
  > default value: ``
  >>
* `DEFAULT_LANG_TRACK`
  > default value: `fr`
  >>
* `KIND_CHOICES`
  > default value: ``
  >>
* `LANG_CHOICES`
  > default value: ``
  >>
* `LINK_SUPERPOSITION`
  > default value: `False`
  >>
* `MODEL_COMPILE_DIR`
  > default value: `/path/of/project/Esup-Pod/compile-model`
  >>
* `PREF_LANG_CHOICES`
  > default value: ``
  >>
* `ROLE_CHOICES`
  > default value: ``
  >>
* `TRANSCRIPTION_MODEL_PARAM`
  > default value: ``
  >>
* `TRANSCRIPTION_TYPE`
  > default value: `STT`
  >>
* `USE_ENRICH_READY`
  > default value: `False`
  >>

### Cut application configuration

Cut application to cut videos.<br>
Set `USE_CUT` to True to activate this application.<br>

* `USE_CUT`
  > default value: `False`
  >> Activation of the Cut application<br>

### Dressing application configuration

Dressing App to customize a video with watermark & credits.<br>
Set `USE_DRESSING` to True to activate this application.<br>

* `USE_DRESSING`
  > default value: `False`
  >> Activation of dressings. Allows users to customize a video with watermark & credits.<br>

### Duplicate application configuration

Duplicate App to create a copy of the form of an existing video<br>
Set `USE_DUPLICATE` to True to activate this application.<br>

* `USE_DUPLICATE`
  > default value: `False`
  >> Activation of duplicate. Allows users to duplicate a video<br>

### 


### Speaker application configuration

Speaker application to add speakers to video.<br>
Set `USE_SPEAKER` to True to activate this application.<br>

* `USE_SPEAKER`
  > default value: `False`
  >> Activation of the Speaker application<br>
* `REQUIRED_SPEAKER_FIRSTNAME`
  > default value: `True`
  >> First name required in the speaker addition form<br>

### Video import application configuration

Import_video app to import external videos into Pod.<br>
Set `USE_IMPORT_VIDEO` to True to activate this application.<br>

* `MAX_UPLOAD_SIZE_ON_IMPORT`
  > default value: `4`
  >> Maximum size in Gb of video files that can be imported into the platform<br>
  >> via the import_video application (0 = no maximum size).<br>
* `RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY`
  > default value: `True`
  >> Only "staff" users will be able to import videos<br>
* `USE_IMPORT_VIDEO`
  > default value: `False`
  >> Activation of the video import application<br>
* `USE_IMPORT_VIDEO_BBB_RECORDER`
  > default value: `False`
  >> Using the bbb-recorder plugin for the video import module;<br>
  >> useful for converting a BigBlueButton presentation into a video file.<br>
* `IMPORT_VIDEO_BBB_RECORDER_PLUGIN`
  > default value: `/home/pod/bbb-recorder/`
  >> bbb-recorder plugin directory (see [jibon57/bbb-recorder](https://github.com/jibon57/bbb-recorder) documentation).<br>
  >> bbb-recorder must be installed in this directory, on all encoding servers.<br>
  >> bbb-recorder creates a Downloads directory, at the same level, which requires disk space.<br>
* `IMPORT_VIDEO_BBB_RECORDER_PATH`
  > default value: `/data/bbb-recorder/media/`
  >> Directory that will contain the video files generated by bbb-recorder.<br>

### 

* `AFFILIATION_EVENT`
  > default value: `['faculty', 'employee', 'staff']`
  >>
* `BROADCASTER_PILOTING_SOFTWARE`
  > default value: `[]`
  >>
* `DEFAULT_EVENT_PATH`
  > default value: ``
  >>
* `DEFAULT_EVENT_THUMBNAIL`
  > default value: `/img/default-event.svg`
  >>
* `DEFAULT_EVENT_TYPE_ID`
  > default value: `1`
  >>
* `DEFAULT_THUMBNAIL`
  > default value: `img/default.svg`
  >>
* `EMAIL_ON_EVENT_SCHEDULING`
  > default value: `True`
  >>
* `EVENT_ACTIVE_AUTO_START`
  > default value: `False`
  >>
* `EVENT_CHECK_MAX_ATTEMPT`
  > default value: `10`
  >>
* `EVENT_GROUP_ADMIN`
  > default value: `event admin`
  >>
* `HEARTBEAT_DELAY`
  > default value: `45`
  >>
* `LIVE_CELERY_TRANSCRIPTION`
  > default value: `False`
  >>
* `LIVE_TRANSCRIPTIONS_FOLDER`
  > default value: ``
  >>
* `LIVE_VOSK_MODEL`
  > default value: `{}`
  >>
* `USE_BBB`
  > default value: `False`
  >> Using BigBlueButton<br>
  >> Withdrawn from Pod version 3.8.2 (replaced by the meetings module)<br>
* `USE_BBB_LIVE`
  > default value: `False`
  >> Using the BigBlueButton webinar delivery system<br>
  >> Withdrawn from Pod version 3.8.2 (replaced by the meetings module)<br>
* `USE_LIVE_TRANSCRIPTION`
  > default value: `False`
  >> Enable auto-transcription for live events<br>
  >>
* `VIEW_EXPIRATION_DELAY`
  > default value: `60`
  >>

### 

* `LTI_ENABLED`
  > default value: `False`
  >>
* `PYLTI_CONFIG`
  > default value: `{}`
  >> The PYLTI_CONFIG variable in your settings.py configures the application consumers and secrets.<br>
  >>
  >> ```python
  >> PYLTI_CONFIG = {
  >>     'consumers': {
  >>         '<random number string>': {
  >>             'secret': '<random number string>'
  >>         }
  >>     }
  >> }
  >> ```
  >>

### 

* `HOMEPAGE_VIEW_VIDEOS_FROM_NON_VISIBLE_CHANNELS`
  > default value: `False`
  >> Display videos from non visible channels on the homepage<br>
* `USE_BBB`
  > default value: `True`
  >>
* `USE_BBB_LIVE`
  > default value: `False`
  >>
* `USE_IMPORT_VIDEO`
  > default value: `False`
  >> Activation of the video import application<br>
* `USE_MEETING`
  > default value: `False`
  >> Activate the meeting application<br>
* `USE_OPENCAST_STUDIO`
  > default value: `False`
  >> Activate the [Opencast](https://opencast.org/) studio.<br>
* `VERSION`
  > default value: ``
  >> Version of the project<br>
* `WEBTV_MODE`
  > default value: `False`
  >> Webtv mode allows you to switch POD into a webtv application removing the connection buttons for example<br>

### 



* `BBB_API_URL`
  > default value: ``
  >>
* `BBB_LOGOUT_URL`
  > default value: ``
  >>
* `BBB_MEETING_INFO`
  > default value: `{}`
  >> list of key:value to get information from session meeting in BBB<br>
* `BBB_SECRET_KEY`
  > default value: ``
  >>
* `DEFAULT_MEETING_THUMBNAIL`
  > default value: `/img/default-meeting.svg`
  >> Default image displayed as a poster or thumbnail, used to present the meeting.<br>
  >> This image must be located in the `static` directory.<br>
* `MEETING_DATE_FIELDS`
  > default value: `()`
  >> list of date fields for the meeting form<br>
  >> the fields are grouped into a fieldset<br>
* `MEETING_DISABLE_RECORD`
  > default value: `True`
  >>
* `MEETING_MAIN_FIELDS`
  > default value: `()`
  >> list the main fields for the meeting session form<br>
  >> the main fields are displayed directly in the form page of a meeting<br>
* `MEETING_MAX_DURATION`
  > default value: `5`
  >> set the max duration for a meeting session<br>
* `MEETING_PRE_UPLOAD_SLIDES`
  > default value: ``
  >>
  >> Pre-loaded slideshow for virtual meetings.<br>
  >> A user can override this value by choosing a slideshow when creating a virtual meeting.<br>
  >> Must be in the static directory.<br>
* `MEETING_RECORD_FIELDS`
  > default value: `()`
  >> list of all fields that will be hidden if `MEETING_DISABLE_RECORD` is set to True.<br>
* `MEETING_RECURRING_FIELDS`
  > default value: `()`
  >> List of all fields involved by the recurring of a meeting<br>
  >> In this case, all this fields are grouped in a fieldset shown in modal<br>
* `RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY`
  > default value: `False`
  >>
* `USE_MEETING_WEBINAR`
  > default value: `False`
  >> Activate Webinar mode for the meetings module<br>
* `MEETING_WEBINAR_SIPMEDIAGW_URL`
  > default value: ``
  >> URL of the SIPMediaGW server that manages webinars (e.g. `https://sipmediagw.univ.fr`)<br>
  >> Retired as of Pod version 3.8.2 (replaced by the meetings module, see live gateway)<br>
* `MEETING_WEBINAR_SIPMEDIAGW_TOKEN`
  > default value: ``
  >> Bearer token for the SIPMediaGW server that manages webinars<br>
  >> Retired as of Pod version 3.8.2 (see live gateway)<br>
* `MEETING_WEBINAR_FIELDS`
  > default value: `("is_webinar", "enable_chat")`
  >> List the additional fields for the webinar session form<br>
  >> the additional fields are displayed directly in the form page of a webinar<br>
* `MEETING_WEBINAR_AFFILIATION`
  > default value: `['faculty', 'employee', 'staff']`
  >> Access groups or affiliations of people authorized to create a webinar<br>
* `MEETING_WEBINAR_GROUP_ADMIN`
  > default value: `webinar admin`
  >> Group of people authorized to create a webinar<br>
* `USE_MEETING`
  > default value: `False`
  >>

### Playlist application configuration

Playlist app for the playlist management.<br>
Set `USE_PLAYLIST` to True to activate this application.<br>

* `COUNTDOWN_PLAYLIST_PLAYER`
  > default value: `0`
  >> Countdown used between each video when playing an autoplay playlist.<br>
  >> The coutdown is not present if it at 0.<br>
* `DEFAULT_PLAYLIST_THUMBNAIL`
  > default value: `/static/playlist/img/default-playlist.svg`
  >> Default image displayed as a poster or thumbnail, used to present the playlist.<br>
  >> This image must be located in the `static` directory.<br>
* `RESTRICT_PROMOTED_PLAYLIST_ACCESS_TO_STAFF_ONLY`
  > default value: `True`
  >> Restrict access to promoted playlists creation to staff only.<br>
* `USE_FAVORITES`
  > default value: `False`
  >> Activation of favorite videos.<br>
  >> Allows users to add videos to their favorites.<br>
* `USE_PLAYLIST`
  > default value: `False`
  >> Activation of playlist. Allows users to add videos in a playlist.<br>
* `USE_PROMOTED_PLAYLIST`
  > default value: `False`
  >> Activation of promoted playlists. Allows users to use the promoted playlists.<br>

### 

* `FILES_DIR`
  > default value: `files`
  >>
* `FILE_ALLOWED_EXTENSIONS`
  > default value: `('doc', 'docx', 'odt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'txt', 'html', 'htm', 'vtt', 'srt')`
  >> Extensions allowed for documents uploaded in the file manager (lowercase).<br>
* `FILE_MAX_UPLOAD_SIZE`
  > default value: `10`
  >> Maximum size in MB per file uploaded in the file manager<br>
* `IMAGE_ALLOWED_EXTENSIONS`
  > default value: `('jpg', 'jpeg', 'bmp', 'png', 'gif', 'tiff', 'webp')`
  >> Allowed extensions for images uploaded in the file manager (must be lowercase).<br>

### 

* `USE_NOTIFICATIONS`
  > default value: `False`
  >>
* `WEBPUSH_SETTINGS`
  > default value:

  ```python
  {
      'VAPID_PUBLIC_KEY': '',
      'VAPID_PRIVATE_KEY': '',
      'VAPID_ADMIN_EMAIL': 'contact@esup-portail.org'
  }
  ```

  >>

### Quiz application configuration

Quiz App to add various questions on videos.<br>
Set `USE_QUIZ` to True to activate this application.<br>

* `USE_QUIZ`
  > default value: `False`
  >> Activation of quizzes. Allows users to create, respond and use quizzes in videos.<br>

### 

* `ALLOW_MANUAL_RECORDING_CLAIMING`
  > default value: `False`
  >>
* `ALLOW_RECORDER_MANAGER_CHOICE_VID_OWNER`
  > default value: `True`
  >> If True, the manager of the recorder can choose the recorder file owner<br>
* `DEFAULT_RECORDER_ID`
  > default value: `1`
  >> Add a default recorder to an unidentifiable recording file.<br>
* `DEFAULT_RECORDER_PATH`
  > default value: `/data/ftp-pod/ftp/`
  >> Root path of the directory where the recordings are deposited<br>
* `DEFAULT_RECORDER_TYPE_ID`
  > default value: `1`
  >> Default video type identifier (if not specified).<br>
* `DEFAULT_RECORDER_USER_ID`
  > default value: `1`
  >> Identifier of the default owner (if not specified) of the deposited records.<br>
* `OPENCAST_DEFAULT_PRESENTER`
  > default value: `mid`
  >>
* `OPENCAST_FILES_DIR`
  > default value: `opencast-files`
  >>
* `OPENCAST_MEDIAPACKAGE`
  > default value: `-> see xml content`
  >> Default content of the xml file to create the mediapackage for the studio. This file will contain all the specifics of the recording (source, cutting, title, presenter etc.)<br>
* `PUBLIC_RECORD_DIR`
  > default value: `records`
  >> Web access path (public) to the recording repository directory (`DEFAULT_RECORDER_PATH`).<br>
  >> Warning: remember to modify the NGINX conf<br>
* `RECORDER_ADDITIONAL_FIELDS`
  > default value: `()`
  >> List of additional fields for the recorders form. This list includes the name of the fields corresponding to the editing parameters of a video (Discipline, Channel, Theme, keywords...).<br>
  >> The following example includes all the possible fields, but can be lightened according to needs.<br>
  >> The videos will then be generated with the values of the additional fields as defined in their recorder.<br>
* `RECORDER_ALLOW_INSECURE_REQUESTS`
  > default value: `False`
  >>
* `RECORDER_BASE_URL`
  > default value: `https://pod.univ.fr`
  >>
* `RECORDER_SELF_REQUESTS_PROXIES`
  > default value: `{"http": None, "https": None}`
  >>
* `RECORDER_SKIP_FIRST_IMAGE`
  > default value: `False`
  >>
* `RECORDER_TYPE`
  > default value: `(('video', _('Video')), ('audiovideocast', _('Audiovideocast')), ('studio', _('Studio')))`
  >> Type of record managed by the platform.<br>
  >> A recorder can only upload files of the type offered by the platform.<br>
  >> The processing is done according to the type of file deposited.<br>
* `USE_OPENCAST_STUDIO`
  > default value: `False`
  >>
* `USE_RECORD_PREVIEW`
  > default value: `False`
  >> If True, displays the video preview icon in the "Claim a recording" page.<br>

### 

* `ACTIVE_VIDEO_COMMENT`
  > default value: `False`
  >>
* `CACHE_VIDEO_DEFAULT_TIMEOUT`
  > default value: `600`
  >>
  >> Time in second to cache video data<br>
* `CHANNEL_FORM_FIELDS_HELP_TEXT`
  > default value: ``
  >>
* `CHUNK_SIZE`
  > default value: `1000000`
  >>
* `CURSUS_CODES`
  > default value: `()`
  >>
* `DEFAULT_DC_COVERAGE`
  > default value: `TITLE_ETB + " - Town - Country"`
  >>
* `DEFAULT_DC_RIGHTS`
  > default value: `BY-NC-SA`
  >>
* `DEFAULT_THUMBNAIL`
  > default value: `img/default.svg`
  >>
* `DEFAULT_TYPE_ID`
  > default value: `1`
  >>
* `DEFAULT_YEAR_DATE_DELETE`
  > default value: `2`
  >>
* `FORCE_LOWERCASE_TAGS`
  > default value: `True`
  >>
* `LANG_CHOICES`
  > default value: ``
  >>
* `LICENCE_CHOICES`
  > default value: `()`
  >>
* `MAX_DURATION_DATE_DELETE`
  > default value: `10`
  >>
* `MAX_TAG_LENGTH`
  > default value: `50`
  >>
* `NOTES_STATUS`
  > default value: `()`
  >>
* `OEMBED`
  > default value: `False`
  >>
* `ORGANIZE_BY_THEME`
  > default value: `False`
  >>
* `RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY`
  > default value: `False`
  >>
* `THEME_FORM_FIELDS_HELP_TEXT`
  > default value: `""`
  >>
* `USER_VIDEO_CATEGORY`
  > default value: `False`
  >>
* `USE_OBSOLESCENCE`
  > default value: `False`
  >>
* `USE_STATS_VIEW`
  > default value: `False`
  >>
* `USE_VIDEO_EVENT_TRACKING`
  > default value: `False`
  >>
* `USE_XAPI_VIDEO`
  > default value: `False`
  >>
  >> Enables sending xAPI statements for the video player.<br>
  >> Attention, you must set USE_XAPI to True for the statements to be sent.<br>
* `VIDEO_ALLOWED_EXTENSIONS`
  > default value: `()`
  >> Allowed extensions for video upload on the platform (lowercase).<br>
* `VIDEO_FEED_NB_ITEMS`
  > default value: `100`
  >>
* `VIDEO_FORM_FIELDS`
  > default value: `__all__`
  >> List of displayed video editing form fields.<br>
* `VIDEO_FORM_FIELDS_HELP_TEXT`
  > default value: ``
  >>
* `VIDEO_MAX_UPLOAD_SIZE`
  > default value: `1`
  >>
* `VIDEO_PLAYBACKRATES`
  > default value: `[0.5, 1, 1.5, 2]`
  >>
* `VIDEO_RECENT_VIEWCOUNT`
  > default value: `180`
  >> Duration (in number of days) over which we wish to count the number of recent views.<br>
* `VIDEO_REQUIRED_FIELDS`
  > default value: `[]`
  >>
* `VIEW_STATS_AUTH`
  > default value: `False`
  >>

### 



* `CAPTIONS_STRICT_ACCESSIBILITY`
  > default value: `False`
  >> If True, subtitles will be generated strictly following accessibility standards.<br>
  >> A warning message will be displayed if the subtitles do not follow these standards,<br>
  >> even if the value is False.<br>
* `CELERY_BROKER_URL`
  > default value: `redis://redis.localhost:6379/5`
  >>
* `CELERY_TO_ENCODE`
  > default value: `False`
  >>
* `DEFAULT_LANG_TRACK`
  > default value: `fr`
  >>
* `EMAIL_ON_ENCODING_COMPLETION`
  > default value: `True`
  >>
* `EMAIL_ON_TRANSCRIPTING_COMPLETION`
  > default value: `True`
  >>
* `ENCODE_STUDIO`
  > default value: `start_encode_studio`
  >>
* `ENCODE_VIDEO`
  > default value: `start_encode`
  >>
* `ENCODING_CHOICES`
  > default value: `()`
  >>
* `ENCODING_TRANSCODING_CELERY_BROKER_URL`
  > default value: `False`
  >>
* `FORMAT_CHOICES`
  > default value: `()`
  >>
* `USE_REMOTE_ENCODING_TRANSCODING`
  > default value: `False`
  >>
* `POD_API_URL`
  > default value: ``
  >> Address of API rest to be called at the end of remote encoding or remote transcription.<br>
  >> Example: `https://pod.univ.fr/rest/`<br>
* `POD_API_TOKEN`
  > default value: ``
  >> Authentication token used for the call at the end of remote encoding or remote transcription.<br>
  >> To create it, go to Admin > Authentication token > token.<br>
* `VIDEO_RENDITIONS`
  > default value: `[]`
  >>

### 

* `ES_INDEX`
  > default value: `pod`
  >>
* `ES_MAX_RETRIES`
  > default value: `10`
  >>
* `ES_TIMEOUT`
  > default value: `30`
  >>
* `ES_URL`
  > default value: `["http://elasticsearch.localhost:9200/"]`
  >>
* `ES_VERSION`
  > default value: `8`
  >>
* `ES_OPTIONS`
  > default value: `{}`
  >>

### 

Application for sending xAPI statements to an LRS.<br>
No statements persist in Pod, they are all sent to the configured LRS.<br>
Please note, Celery must be set to send statements.<br>

* `USE_XAPI`
  > default value: `False`
  >>
* `XAPI_ANONYMIZE_ACTOR`
  > default value: `True`
  >>
* `XAPI_LRS_LOGIN`
  > default value: ``
  >>
* `XAPI_LRS_PWD`
  > default value: ``
  >>
* `XAPI_LRS_URL`
  > default value: ``
  >>
