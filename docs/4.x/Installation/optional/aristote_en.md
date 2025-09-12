---
layout: default
version: 4.x
lang: en
---

# Implementation of enrichment via the Aristote AI

> 💡 This section applies only to ESUP-Pod Versions 3.7.0 and later.

## Introduction

This module enables enriching videos with the Aristote AI developed by Centrale Supelec ([disi.pages.centralesupelec.fr](https://disi.pages.centralesupelec.fr/innovation/aristote/aristote-website)). The enrichments allow, in particular, the automatic generation of metadata (title, description and keywords), a transcription as well as a quiz from the audio track of the video.

Technically, enrichment requests are made at the initiative of the video owners from their editing page. A request is then sent to the Aristote server with, as parameters, the URL of an audio file (corresponding to the video's audio track) and a notification URL that will be contacted by Aristote once the processing has been completed.

## Prerequisites

The URLs sent to Aristote for retrieving the audio file and for treatment notification must be accessible from anywhere in the world because it is currently not possible to filter requests made by Aristote in response to enrichment requests. This is due to Aristote's infrastructure (based on Kubernetes), which automatically creates or removes backend servers depending on load.

These backend servers do not have a predictable IP and send requests directly without going through a proxy that would allow having a fixed and reliable originating address (which could be filtered).

Up to POD version 3.8.1, these URLs begin with the domain name of the POD server querying Aristote. This server must therefore be accessible from the entire world (which can be problematic for test servers whose access is often limited to the host institution's internal network).

## Configuration

To enable the feature, the following variables must be set in the file `pod/custom/settings_local.py`:

- `USE_AI_ENHANCEMENT = True` # Activation of the feature
- `AI_ENHANCEMENT_API_URL = 'https://api.aristote.education/api'` # URL to contact the Aristote API
- `AI_ENHANCEMENT_CLIENT_ID = 'univ_client_id'`
- `AI_ENHANCEMENT_CLIENT_SECRET = 'xxx-xxx-xxx'`
- `AI_ENHANCEMENT_API_VERSION = 'v1'` # Version of the Aristote API used for enrichment

To obtain the values to set for the variables `AI_ENHANCEMENT_CLIENT_ID` and `AI_ENHANCEMENT_CLIENT_SECRET`, a request for access to the Aristote API must be made through Centrale Supelec (contact.aristote [at] centralesupelec.fr).

Additional variables (useful but not required for operation) can also be added:

- `AI_ENHANCEMENT_CGU_URL = 'https://disi.pages.centralesupelec.fr/innovation/aristote/aristote-website/utilisation_service'` # URL of the terms of use page for the Aristote AI
- `AI_ENHANCEMENT_FIELDS_HELP_TEXT = ''` # Customization of the wording used to describe the input fields on the enrichment request form
- `AI_ENHANCEMENT_TO_STAFF_ONLY = True` # Restriction (or not) of access to the feature to users with the "Team" role
