# Esup Pod - Apps Configuration

## Authentication Configuration

Authentication application configuration

* `AFFILIATION_STAFF`
  > default value: `['faculty', 'employee', 'staff']`
  >>
* `ALLOWED_SUPERUSER_IPS`
  > default value: `['127.0.0.1', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']`
  >> List of IPs and/or ranges from which “superuser” status is allowed.
* `CAS_ADMIN_REDIRECT`
  > default value: `False`
  >> Redirect to CAS login for admin interface.
* `CAS_APPLY_ATTRIBUTES_TO_USER`
  > default value: `True`
  >> Automatically apply attributes returned by CAS to the user profile.
* `CAS_FORCE_CHANGE_USERNAME_CASE`
  > default value: `lower`
  >> Force case (lower or upper case) of CAS username.
* `CAS_SERVER_URL`
  > default value: `https://cas.example.org`
  >> Url of the institution’s CAS server.
* `CAS_VERSION`
  > default value: `3`
  >> CAS protocol version.
* `CREATE_GROUP_FROM_AFFILIATION`
  > default value: `True`
  >>
* `CREATE_GROUP_FROM_GROUPS`
  > default value: `True`
  >>
* `HIDE_USERNAME`
  > default value: `False`
  >>
* `LDAP_BIND_DN`
  > default value: `cn=pod,ou=app,dc=example,dc=com`
  >> Identifiant (DN) of the account to connect to the LDAP server.
* `LDAP_BIND_PASSWORD`
  > default value: ``
  >> Password of the account to connect to the LDAP server.
* `LDAP_MAPPING_ATTRIBUTES`
  > default value: `{'uid': 'uid', 'mail': 'mail', 'last_name': 'sn', 'first_name': 'givenname', 'primaryAffiliation': 'eduPersonPrimaryAffiliation', 'affiliations': 'eduPersonAffiliation', 'groups': 'memberOf', 'establishment': 'establishment'}`
  >> Mapping between LDAP attributes and Pod account fields.
* `LDAP_SERVER_PORT`
  > default value: `389`
  >> LDAP server port.
* `LDAP_SERVER_URL`
  > default value: `ldap://ldap.example.org`
  >> LDAP server URL.
* `LDAP_SERVER_USE_SSL`
  > default value: `False`
  >> Use SSL for LDAP connection.
* `LDAP_USER_SEARCH_BASE`
  > default value: `ou=people,dc=example,dc=com`
  >> LDAP search base for users.
* `LDAP_USER_SEARCH_FILTER`
  > default value: `(uid=%(uid)s)`
  >> LDAP filter for searching the individual in the LDAP server.
* `OIDC_CLAIM_FAMILY_NAME`
  > default value: `family_name`
  >> Claim name for family name.
* `OIDC_CLAIM_GIVEN_NAME`
  > default value: `given_name`
  >> Claim name for first name.
* `OIDC_CLAIM_PREFERRED_USERNAME`
  > default value: `preferred_username`
  >> Claim name for username.
* `OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES`
  > default value: `[]`
  >> Default access groups assigned to OIDC users.
* `OIDC_DEFAULT_AFFILIATION`
  > default value: `member`
  >> Default affiliation for OIDC users.
* `OIDC_NAME`
  > default value: `OpenID Connect`
  >> Display name for OpenID Connect authentication.
* `OIDC_OP_TOKEN_ENDPOINT`
  > default value: `https://auth.example.org/oidc/token`
  >> OIDC Provider Token endpoint.
* `OIDC_OP_USER_ENDPOINT`
  > default value: `https://auth.example.org/oidc/userinfo`
  >> OIDC Provider UserInfo endpoint.
* `OIDC_RP_CLIENT_ID`
  > default value: `my-client-id`
  >> OIDC Client ID.
* `OIDC_RP_CLIENT_SECRET`
  > default value: `my-secret`
  >> OIDC Client Secret.
* `REMOTE_USER_HEADER`
  > default value: `REMOTE_USER`
  >>
* `SHIBBOLETH_ATTRIBUTE_MAP`
  > default value: `{'REMOTE_USER': [True, 'username'], 'Shibboleth-givenName': [True, 'first_name'], 'Shibboleth-sn': [False, 'last_name'], 'Shibboleth-mail': [False, 'email'], 'Shibboleth-primary-affiliation': [False, 'affiliation'], 'Shibboleth-unscoped-affiliation': [False, 'affiliations']}`
  >> Mapping between Shibboleth attributes and user model.
* `SHIBBOLETH_STAFF_ALLOWED_DOMAINS`
  > default value: `[]`
  >>
* `SHIB_NAME`
  > default value: `Identify Federation`
  >> Display name for Shibboleth authentication.
* `SHIB_SECURE_HEADER`
  > default value: `None`
  >> Secure header for Shibboleth.
* `SHIB_SECURE_VALUE`
  > default value: `secure`
  >> Expected value for Shibboleth secure header.
* `USE_CAS`
  > default value: `False`
  >>
* `USE_ESTABLISHMENT_FIELD`
  > default value: `False`
  >>
* `USE_LDAP`
  > default value: `False`
  >> Enable LDAP authentication.
* `USE_LOCAL_AUTH`
  > default value: `True`
  >> Enable local authentication (username/password stored in database).
* `USE_OIDC`
  > default value: `False`
  >>
* `USE_SHIB`
  > default value: `False`
  >>

## Video Configuration

Video application configuration

* `ALLOWED_EXTENSIONS`
  > default value: `['3gp', 'avi', 'divx', 'flv', 'm2p', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'mts', 'wmv', 'mp3', 'ogg', 'wav', 'wma', 'webm', 'ts']`
  >> Allowed file extensions for upload.
* `ALLOW_AUTHENTICATED_UPLOAD`
  > default value: `True`
  >> Allow all authenticated users to upload videos.
* `CACHE_TIMEOUT`
  > default value: `600`
  >> Time in seconds to cache video data.
* `CHANNEL_MODE`
  > default value: `False`
  >> Enable channel display mode.
* `CHUNK_SIZE`
  > default value: `100000`
  >>
* `DEFAULT_LICENSE`
  > default value: ``
  >> Default license for new videos.
* `FFPROBE_GET_INFO`
  > default value: `high`
  >> Detail level for metadata extraction.
* `FORCE_LOWERCASE_TAGS`
  > default value: `True`
  >>
* `HIDE_CURSUS`
  > default value: `False`
  >>
* `HIDE_DISCIPLINES`
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
* `HIDE_USER_FILTER`
  > default value: `False`
  >>
* `HOMEPAGE_SHOWS_PASSWORDED`
  > default value: `False`
  >>
* `MAX_TAG_LENGTH`
  > default value: `50`
  >>
* `MAX_UPLOAD_SIZE_GB`
  > default value: `1`
  >>
* `NUMBER_TAGS_CLOUD`
  > default value: `20`
  >> Number of tags displayed in the cloud.
* `RESTRICT_EDIT_TO_STAFF`
  > default value: `False`
  >>
* `THUMBNAILS_DIR`
  > default value: `thumbnails`
  >> Directory for storing video thumbnails.
* `USER_QUOTA_SIZE_GB`
  > default value: `5`
  >> Storage quota per user in GB.
* `USER_VIDEO_CATEGORY`
  > default value: `False`
  >>
* `USE_CUT`
  > default value: `False`
  >>
* `USE_DUPLICATE`
  > default value: `False`
  >>
* `USE_HYPERLINKS`
  > default value: `False`
  >> Enable video hyperlinks feature.
* `USE_STATS_VIEW`
  > default value: `False`
  >>
* `VIDEOS_DIR`
  > default value: `videos`
  >>
* `VIDEO_REQUIRED_FIELDS`
  > default value: `[]`
  >>
* `VIEW_STATS_AUTH`
  > default value: `False`
  >>
* `WEBTV_MODE`
  > default value: `False`
  >>

## API Configuration

API documentation settings.

* `SPECTACULAR_SETTINGS`
  > default value: `{'TITLE': 'Pod REST API', 'DESCRIPTION': 'Video management API (Local Authentication)', 'SERVE_INCLUDE_SCHEMA': False, 'COMPONENT_SPLIT_REQUEST': True}`
  >> Configuration for OpenAPI schema generation.

## Core Configuration

Core application configuration

* `MEDIA_ROOT`
  > default value: `media`
  >> Absolute filesystem path to the directory that will hold user-uploaded files.
* `MEDIA_URL`
  > default value: `/media/`
  >> URL that handles the media served from MEDIA_ROOT.
* `STATIC_ROOT`
  > default value: `staticfiles`
  >> The absolute path to the directory where collectstatic will collect static files for deployment.
* `STATIC_URL`
  > default value: `/static/`
  >> URL to use when referring to static files located in STATIC_ROOT.

## Completion Configuration

Completion application configuration

* `DEFAULT_LANG_TRACK`
  > default value: `fr`
  >> Default language for new subtitle tracks.
* `KIND_CHOICES`
  > default value: `[['subtitles', "_('Subtitles')"], ['captions', "_('Captions')"]]`
  >> Available kinds for subtitle tracks.
* `LINK_SUPERPOSITION`
  > default value: `False`
  >> Enable automatic conversion of URLs into links in overlays.
* `REQUIRED_SPEAKER_FIRSTNAME`
  > default value: `True`
  >> Make the first name of a speaker mandatory.
* `ROLE_CHOICES`
  > default value: `[['actor', "_('Actor')"], ['author', "_('Author')"], ['consultant', "_('Consultant')"], ['contributor', "_('Contributor')"], ['director', "_('Director')"], ['speaker', "_('Speaker')"], ['technician', "_('Technician')"], ['voice-over', "_('Voice-over')"]]`
  >> Available roles for contributors.
* `USE_SPEAKER`
  > default value: `False`
  >> Enable or disable the Speakers module.
