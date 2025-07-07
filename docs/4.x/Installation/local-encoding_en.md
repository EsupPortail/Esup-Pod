---
layout: default
version: 4.x
lang: en
---

# Local encoding management

By default, the application executes the encoding and transcription tasks on the **same machine** as the one it is running on.

If encoding is performed on the same machine as the front-end, their execution is "threaded" (executed in a sub-process).

To configure these tasks and their execution, you can refer to the configuration file available at this address:

[https://github.com/EsupPortail/Esup-Pod/blob/master/CONFIGURATION_EN.md#encoding](https://github.com/EsupPortail/Esup-Pod/blob/master/CONFIGURATION_EN.md#encoding)

Configuration is carried out in your ``custom/settings_local.py``, in particular for the following parameters:

```sh
# Not to use traditional remote encoding
CELERY_TO_ENCODE = False
# Not to use microservice encoding
USE_REMOTE_ENCODING_TRANSCODING = False
# Function called to start video encoding
ENCODE_VIDEO = "start_encode"
```
