---
layout: default
version: 4.x
lang: en
---

# Setting up a live broadcast

## Installing a New VM

> 💡 We recommend setting up the live stream on a separate VM from Pod.

The live stream is based on the Nginx RTMP module.

## Prerequisites

- Installation: documentation was originally created on Debian 9.4 64-bit.

To install nginx version 1.14, you must first add the **backports** repository:

Switch to root user (sudo -s)

```bash
$> vim /etc/apt/sources.list
```

Add the line: `deb http://ftp.debian.org/debian stretch-backports main`

Then update:

```bash
$> apt update
```

## Installing nginx

```bash
$> apt-get -t stretch-backports install nginx
```

Next, install the nginx-rtmp module:

```bash
$> apt-get install libnginx-mod-rtmp
```

## ffmpeg

For multi-bitrate, install ffmpeg which encodes the video stream in real-time:

```bash
$> aptitude install ffmpeg
```

To verify everything went well, list the contents of the nginx enabled modules directory:

```bash
$> ls -l /etc/nginx/modules-enabled/
```

You should see mod-rtmp.conf:

```bash
total 16
[...]
lrwxrwxrwx 1 root root 48 Oct  17 12:59 50-mod-rtmp.conf -> /usr/share/nginx/modules-available/mod-rtmp.conf
[...]
```

Next, add the `include rtmp` instruction in nginx.conf and create the corresponding snippets:

```bash
$> vim /etc/nginx/nginx.conf
[...]
include /etc/nginx/snippets/rtmp.conf;
[...]
```

Then, create the **RTMP** snippet:

```bash
$> vim /etc/nginx/snippets/rtmp.conf
```

### Original `rtmp.conf` File

Below is the original configuration file which uses **3 encodings** and is not specifically optimized for latency (expect **between 15 and 30 seconds of latency** with this configuration):

#### File `/etc/nginx/snippets/rtmp.conf`

```bash
rtmp {
    server {
        listen 1935; # default rtmp port
        chunk_size 4096; # packet size transmitted/fragmented

         application live { # application name
            live on;
            #meta copy;
            #record off;

            # publish only from localhost
            allow publish 127.0.0.1; # only publish locally
            allow publish all; # everyone can publish
            allow play all; # certain IP addresses are allowed to read
            deny publish all; # add a deny at the end for security

            exec ffmpeg -i rtmp://localhost/$app/$name
                -c:v libx264 -preset veryfast -b:v 256k -maxrate 256k -bufsize 512k -vf "scale=480:-2,format=yuv420p" -g 60 -c:a aac -b:a 64k -ar 44100 -f flv rtmp://localhost/show/$name_low
                -c:v libx264 -preset veryfast -b:v 512k -maxrate 512k -bufsize 1024k -vf "scale=720:-2,format=yuv420p" -g 60 -c:a aac -b:a 96k -ar 44100 -f flv rtmp://localhost/show/$name_mid
                -c:v libx264 -preset veryfast -b:v 1024k -maxrate 1024k -bufsize 2048k -vf "scale=1280:-2,format=yuv420p" -g 60 -c:a aac -b:a 128k -ar 44100 -f flv rtmp://localhost/show/$name_high
            >/tmp/ffmpeg.log 2>&1 ;

            exec_publish curl --request PATCH "https://pod.univ.fr/rest/broadcasters/$name/" --header "Content-Type: application/json" --header "Accept: application/json" --user CHANGE_USERNAME:CHANGE-THIS-STATUS-PASSWORD --data "{"status":true}";

            exec_publish_done curl --request PATCH "https://pod.univ.fr/rest/broadcasters/$name/" --header "Content-Type: application/json" --header "Accept: application/json" --user CHANGE_USERNAME:CHANGE-THIS-STATUS-PASSWORD --data "{"status":false}";
        }

        # This application is for splitting the stream into HLS fragments
        application show {
            live on; # Allows live input from above
            meta copy;
            record off;

            hls on; # enable hls
            hls_path /dev/shm/hls; # path for ts fragments, put in /dev/shm to avoid overworking the disk
            hls_nested on; # creates a subdirectory per stream sent
            hls_fragment 2s; # fragment size

            # Instruct clients to adjust resolution according to bandwidth
            hls_variant _low BANDWIDTH=320000; # Low bitrate, sub-SD resolution
            hls_variant _high BANDWIDTH=640000; # High bitrate, higher-than-SD resolution
            hls_variant _src BANDWIDTH=1200000; # Source bitrate, source resolution
        }
    }
}
```

> 💡 This configuration is well-proven over time, but consumes more resources (3 encodings) with some final latency.

### Optimized rtmp.conf File for Reduced Latency

Below is the same configuration file which uses **2 encodings** and is specifically optimized for latency (expect **less than 10 seconds of latency** with this configuration).

This file incorporates configuration elements presented by Ludovic Bouguerra from the company Kalyzée during his Webinar "Setting up a live infrastructure and reducing latency with Pod" on September 23, 2022.

The modified configuration elements are as follows:

- 2 encodings performed
- preset set to ultrafast
- tune zerolatency option
- number of keyframes (-g) set to 60 (or 50)

Which gives:

#### File `/etc/nginx/snippets/rtmp.conf` (Reduced latency)

```bash
rtmp {
    server {
        listen 1935; # default rtmp port
        chunk_size 4000; # packet size transmitted/fragmented

         application live { # application name
            live on;
            #meta copy;
            #record off;

            # publish only from localhost
            allow publish 127.0.0.1; # only publish locally
            allow publish all; # everyone can publish
            allow play all; # certain IP addresses are allowed to read
            deny publish all; # add a deny at the end for security

            exec ffmpeg -i rtmp://localhost/$app/$name
                -c:v libx264 -preset ultrafast -b:v 512k -tune zerolatency -maxrate 512k -bufsize 1024k -vf "scale=480:-2,format=yuv420p" -g 60 -c:a aac -b:a 96k -ar 44100 -f flv rtmp://localhost/show/$name_low
                -c:v libx264 -preset ultrafast -b:v 1.5M -tune zerolatency -maxrate 1.5M -bufsize 3M -vf "scale=1280:-2,format=yuv420p" -g 60 -c:a aac -b:a 128k -ar 44100 -f flv rtmp://localhost/show/$name_high
            >/tmp/ffmpeg.log 2>&1 ;

            exec_publish curl --request PATCH "https://pod.univ.fr/rest/broadcasters/$name/" --header "Content-Type: application/json" --header "Accept: application/json" --user CHANGE_USERNAME:CHANGE-THIS-STATUS-PASSWORD --data "{"status":true}";

            exec_publish_done curl --request PATCH "https://pod.univ.fr/rest/broadcasters/$name/" --header "Content-Type: application/json" --header "Accept: application/json" --user CHANGE_USERNAME:CHANGE-THIS-STATUS-PASSWORD --data "{"status":false}";
        }

        # This application is for splitting the stream into HLS fragments
        application show {
            live on; # Allows live input from above
            meta copy;
            record off;

            hls on; # enable hls
            hls_path /dev/shm/hls; # path for ts fragments, put in /dev/shm to avoid overworking the disk
            hls_nested on; # creates a subdirectory per stream sent
            hls_fragment 2s; # fragment size
            # Commented out following problems related to RTMP publishing from SMP 351
            # hls_max_fragment 3s;
            # hls_playlist_length 10s;

            # Instruct clients to adjust resolution according to bandwidth
            hls_variant _low BANDWIDTH=512000; # Low/Mid bitrate, about sub-SD resolution
            hls_variant _high BANDWIDTH=1500000; # Source bitrate, source resolution
        }
    }
}
```

> 💡 This configuration is more recent, consumes fewer resources (2 encodings), with reduced final latency.
>
> ⚠️ After deployment in production, it was found that, during RTMP publishing from SMP 351, this configuration could cause an error of the type "**force fragment split**".
>
> Finally, by commenting out the following parameters, this problem no longer reappeared:
>
> ```bash
> # hls_max_fragment 3s;
>
> # hls_playlist_length 10s;
> ```

You can see all the directives for this module at this address: [https://github.com/arut/nginx-rtmp-module/wiki/Directives](https://github.com/arut/nginx-rtmp-module/wiki/Directives)

## HTTP

Finally, declare the `hls` route to read the videos:

```bash
$> vim /etc/nginx/sites-enabled/default
```

### File `/etc/nginx/sites-enabled/default`

```bash
server {
  listen 80 default_server;
  root /var/www/html;
  index index.html index.htm index.nginx-debian.html;
  server_name _;
  location / {
      try_files $uri $uri/ =404;
   }
 # path to HLS application service
        location /hls {
            types {
                application/vnd.apple.mpegurl m3u8;
                video/mp2t ts;
            }
            alias /dev/shm/hls;
            add_header Cache-Control no-cache;
            add_header 'Access-Control-Allow-Origin' 'https://pod.univ-machin.fr';  #  <--- Absolutely not "*": risk of code injection!!!
        }
  add_header 'Access-Control-Allow-Origin' 'https://pod.univ-machin.fr'; # Hotfix for streaming from another server  <--- Absolutely not "*": risk of code injection!!!
}
```

> ⚠️  If your POD frontend is HTTPS, you need to configure Nginx on the live server to serve HTTPS and not HTTP.

## On Your POD Instance

First, activate the live application by adding "live" to THIRD_PARTY_APPS in the settings_local.py file

```bash
...
THIRD_PARTY_APPS = ["xxx","xxx","live"]
...
```

## Managing Live Stream Piloting and Recording Management

First, add the type of streaming hardware you have (currently 2 choices).

This will limit the choices in the site admin

```bash
...
BROADCASTER_PILOTING_SOFTWARE = ['Wowza', 'SMP']
...
```

Then go to the Pod administration:

- create a building
- then a broadcaster attached to that building, specifying the live stream playback URL

**Important**, depending on the type of hardware chosen, you will need to specify the configuration in json (in `Piloting configuration settings`).

The list of parameters to declare is offered when selecting a hardware type.

Here is an example configuration for the two supported hardware types.

This allows controlling the start and stop of recording.

### Example

```bash
# example for WOWZA:
{
  "server_url":"http://stream01.univ.fr:8087",
  "application":"salles_video",
  "livestream":"sallevideo.stream"
}

# example for SMP:
{
  "server_url":"http://xxx.xxx.xx.x",
  "sftp_port":"22022",
  "user":"admin_account",
  "password":"admin_pwd",
  "record_dir_path":"/recordings",
  "rtmp_streamer_id":"1",
  "use_opencast":"true"
}
```

### with WOWZA

Here the file system on which the video file is stored must be shared between Wowza and Pod.

Set it in "DEFAULT_EVENT_PATH" of the `settings_local.py` file

### with SMP Extron

if you use SMPs you can retrieve the video file from an event (live) in 2 ways:

#### Retrieval via SFTP

Pod connects to the SMP server to retrieve the video file and encode it as a video linked to the event).

In the broadcaster’s json configuration:

- verify that the port is declared and open between the two servers
- `use_opencast` must be false
- `rtmp_streamer_id` can be empty

### #Retrieval via the **openCast (studio)** module (From 3.7.0)

The SMP, if it has the push functionality (Extron 351 model for example), sends the file directly to Pod’s studio which will encode it and link it to the event.

In the broadcaster’s json configuration:

- `use_opencast` must be "true"
- `sftp_port` can be empty
- `rtmp_streamer_id` must be correctly set

To find the `rtmp_streamer_id`, you can call the following URL of your SMP and see which streamer is configured in rtmp (in the `pub_url`):

<http://xxx.xxx.xx.x/api/swis/resources?uri=/streamer/rtmp/1&uri=/streamer/rtmp/2&uri=/streamer/rtmp/3&uri=/streamer/rtmp/4&uri=/streamer/rtmp/5&uri=/streamer/rtmp/6>

You must also add a Recorder in the Pod admin with the IP of the SMP (define a Salt, Login, Password)

On the SMP side you must:

- Enable (or install) the Opencast plugin from the hardware management interface (Configuration -> Advanced Features)
- Configure publication towards Pod’s Opencast (Scheduled Events -> Publish Settings -> Active Profiles )
  - Opencast Server Address = Pod’s address
  - Username and Password = those defined in the Recorder
- Test the connection to validate the settings

## Setting Up Viewer Counting (From 2.7.0 and above)

Pod includes a function that allows counting viewers on a live stream in real time.

This functionality must be set up as follows:

- Add a periodic CRON task; every minute is recommended, but it is possible to increase or decrease the time and adjust the settings on pod accordingly (see the following points ...):

```bash
bash -c 'export WORKON_HOME=/home/pod/.virtualenvs; export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3.11; cd /home/pod/django_projects/podv4; source /usr/local/bin/virtualenvwrapper.sh; workon django_pod4; python manage.py live_viewcounter'
```

> ⚠️ WARNING: You may need to modify this command depending on your POD installation paths.

- Set the `HEARTBEAT_DELAY` setting, this defines the delay between which a client will send its "signal" to the server. It is set by default to 45 seconds.
- Set the `VIEW_EXPIRATION_DELAY` setting, it defines the maximum delay for which a view will still be considered present on the live stream.

> To better understand these delay concepts, here is an example with the default parameters: The client (the terminal on which the user is watching the live stream) will send a signal to the Pod server periodically every **45** (HEARTBEAT_DELAY) seconds. Every **minute** (CRON time), a task checks the validity of each viewer to determine if they are still present on the live stream. To do this, it eliminates all viewers who have not sent a signal for **60** (VIEW_EXPIRATION_DELAY) seconds.

**Note**: It is possible to modify the delays to deal with potential performance issues due to the reporting of views. If you encounter difficulties at this level, do not hesitate to double the delays. The counting will be less precise in real time but you will gain in number of requests.

## Broadcasting a Live Video Stream (with OBS)

With **OBS**, in the settings, Stream tab, I specify this data:

- **URL**: rtmp://server.univ.fr/live
- **Stream key**: nico

In **Pod**, in my broadcaster’s settings, in the URL field, I will specify this: <http://server.univ.fr/hls/nico.m3u8>

The short title must be the same as the stream/key (here **nico**) so that the live status can be modified by the REST call ( `exec_publish curl ...)`)

We have just created a live stream accessible in HTML5, multi-bitrate and adaptive, here is the content of the nico.m3u8 file:

### File `nico.m3u8`

```bash
      #EXTM3U
      #EXT-X-VERSION:3
      #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=320000
      nico_low/index.m3u8

      #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=640000
      nico_high/index.m3u8

      #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1200000
      nico_src/index.m3u8
```
