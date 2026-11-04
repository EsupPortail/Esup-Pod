---
layout: default
version: 4.x
lang: en
---

# Compatibility and Prerequisites

## Which Linux kernel and version can I use with Esup-Pod v4?

Esup-Pod v4 has been installed and tested on Debian 11 / Bullseye, Debian 12 / Bookworm and Debian 13 / Trixie versions.

> ⚠️ Although it is possible to install Esup-Pod 4 on other kernels, the commands - displayed in the documentation - have been run on a Debian 11, 12 or 13 distribution.

💡It is recommended to take the latest stable version of Debian.
See [https://www.debian.org/releases/index.en.html](https://www.debian.org/releases/index.en.html)
As of the writing of this documentation, this would be Debian 12 / Bookworm.
{: .alert .alert-info}

## Which version of Python can I use with Esup-Pod v4?

| Esup-Pod Version   | Supported Python Versions           |
|--------------------|-------------------------------------|
| 4.0.x et 4.1.x     | 3.9, 3.10, 3.11, 3.12               |
| 4.2.x à 4.4.x      | 3.10, 3.11, 3.12                    |
| 4.5                | 3.11, 3.12                          |
{: .table .table-striped}

💡It is recommended to take the latest stable version of Python that is supported by Django.
See [https://docs.djangoproject.com/en/5.0/faq/install/#what-python-version-can-i-use-with-django](https://docs.djangoproject.com/en/5.0/faq/install/#what-python-version-can-i-use-with-django)
As of the writing of this documentation, this would be version 3.12.
{: .alert .alert-info}
