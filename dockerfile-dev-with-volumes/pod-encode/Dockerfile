#------------------------------------------------------------------------------------------------------------------------------
#  (\___/)
#  (='.'=) Dockerfile multi-stages node & python
#  (")_(")
#------------------------------------------------------------------------------------------------------------------------------
# Conteneur node
ARG PYTHON_VERSION
# TODO
#FROM harbor.urba.univ-lille.fr/store/node:19 as source-build-js

#------------------------------------------------------------------------------------------------------------------------------
# Conteneur python
FROM $PYTHON_VERSION
WORKDIR /tmp/pod
COPY ./pod/ .
# TODO
#FROM harbor.urba.univ-lille.fr/store/python:3.7-buster

RUN apt-get clean && apt-get update \
    && apt-get install -y netcat \
                          ffmpeg \
                          ffmpegthumbnailer \
                          imagemagick

WORKDIR /usr/src/app

COPY ./requirements-encode.txt .

RUN pip3 install --no-cache-dir -r requirements-encode.txt

# ENTRYPOINT :
COPY ./dockerfile-dev-with-volumes/pod-encode/my-entrypoint-encode.sh /tmp/my-entrypoint-encode.sh
RUN chmod 755 /tmp/my-entrypoint-encode.sh

ENTRYPOINT ["bash", "/tmp/my-entrypoint-encode.sh"]