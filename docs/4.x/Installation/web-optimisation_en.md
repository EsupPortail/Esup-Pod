---
layout: default
version: 4.x
lang: en
---

# Web optimisation

> 💡Documentation to be revised for v4.

In order to optimise our pod servers as much as possible, I invite you to share what you have done to optimise your server.

## Foreword

If you would like to know how your Pod server is performing in terms of optimisation, I suggest testing it using PageSpeed, for example:

[https://developers.google.com/speed/pagespeed/insights](https://developers.google.com/speed/pagespeed/insights)

For reference, the [pod.univ-lille.fr](http://pod.univ-lille.fr) server had the following scores in February 2021 (pod v2.7.3.1):

- Home page: mobile 66% / desktop 88%
- On a video: mobile 31% / desktop 71%

(the higher the score, the better)

## In Nice

Before any optimisation, we had the following results:

- For a link to a video: mobile 22% / desktop 57%
- Home page: we didn’t look![(wink)](http://www.esup-portail.org/wiki/s/9j7max/9111/1h7j1tb/_/images/icons/emoticons/wink.svg)

At the Nginx level, here is what we did:

1. ### Tell nginx to serve compressed versions of static files

With this, when nginx finds a `file.css.gz` file in the static folder, it sends it instead of the standard version (the browser will decompress it)

#### pod_nginx.conf

```bash
location /static {
    gzip_static  on;
    gzip_types text/plain application/xml text/css text/javascript application/javascript image/svg+xml;
    [...]
}
```

For this to work properly, you must of course have ‘.gz’ files, so we manually run a shell script:

#### compress_static.sh

```bash
#!/bin/bash
# Generate compressed versions of all static files to be served by nginx
cd podv4/pod/static/
for file in $(find . -type f)
do
    if [[ $file =~ .*\.(css|js|svg)$ ]]
    then
        gzip -fk ‘$file’
    fi
done
```

==\> this step may be unnecessary once [https://github.com/whs/django-static-compress](https://github.com/whs/django-static-compress) is installed

### 2. Enable on-the-fly compression by nginx of non-static text content

To optimise bandwidth, we can also improve performance by asking nginx to compress text content on the fly. Here is what we added to pod\_nginx.conf:

#### compression in pod_nginx.conf

```bash
    # Django media
    location /media {
        gzip on;
        gzip_types text/vtt;
        [...]
    }
    [...]
    # Finally, send all non-media requests to the Django server.
    location / {
        gzip on;
        uwsgi_pass  django;
        [...]
    }
```

Note: to ensure that vtt files are recognised as text, we added them as ‘text/vtt’ in `/etc/ningx/mime.types`.

### 3. Caching

We defined the following caching policy (1 year on /media, 60 days on /static):

For more information on the importance of setting ‘expires’, please refer to this document: [Avoiding unpredictable caching of static files](http://www.esup-portail.org/wiki/spaces/DOC/pages/967737345/%C3%89viter+les+mises+en+cache+de+dur%C3%A9e+impr%C3%A9visible+des+fichiers+statiques)

#### Caching in `pod_nginx.conf`

```bash
location /media {
    expires 1y;
    add_header Cache-Control ‘public’;
    [...]
}
location /static {
    expires 60d;
    add_header Cache-Control ‘public’;
    [..]
}
```

==\> With all these changes, we went from a score of 22/57 to 40/77 (mobile/desktop) in Nice.

On the home page, we are now at 81%/95%.
