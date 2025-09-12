---
layout: default
version: 4.x
lang: en
---

# Import from Panopto

To import videos from Panopto, I recommend using their SOAP API. There is also a REST API, but it does not allow downloads.

See the documentation for this Panopto SOAP API: [https://support.panopto.com/resource/APIDocumentation/Help/html/40d6edb9-fe7d-1db1-04a7-c3bffd218290.htm] (https://support.panopto.com/resource/APIDocumentation/Help/html/40d6edb9-fe7d-1db1-04a7-c3bffd218290.htm)

You can find an example script for querying their API in Python on Github. (_Please note: the Master branch is for Python 2 and dates from 2019. Use the more recent ‘python3’ branch instead_).

As an example, I am sharing the scripts we used to import Panopto sessions into a local pivot database in order to export json files that we then imported into Pod by following the documentation on migrating from version 1.x to 2.x.

These scripts are far from perfect, but they may serve as a basis if you decide to undertake this task: [https://github.com/Badatos/panopto-soap](https://github.com/Badatos/panopto-soap)

> ⚠️ This migration was carried out in 2022, so it is necessary to take into account the changes in the Pod and Panopto versions when running this script.
