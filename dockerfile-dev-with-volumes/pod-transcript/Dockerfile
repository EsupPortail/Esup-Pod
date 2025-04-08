#------------------------------------------------------------------------------------------------------------------------------
#  (\___/)
#  (='.'=) Dockerfile multi-stages node & python
#  (")_(")
#------------------------------------------------------------------------------------------------------------------------------
# Conteneur node
ARG PYTHON_VERSION=3.9

#------------------------------------------------------------------------------------------------------------------------------
# Conteneur python
FROM $PYTHON_VERSION
WORKDIR /tmp/pod
COPY ./pod/ .
# TODO
#FROM harbor.urba.univ-lille.fr/store/python:3.7-buster

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        netcat \
        sox \
        libsox-fmt-mp3 \
    && apt-get clean\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY ./requirements-encode.txt .
COPY ./requirements-transcripts.txt .

RUN pip3 install --no-cache-dir -r requirements-transcripts.txt \
    && pip3 install --no-cache-dir -r requirements-encode.txt

# ENTRYPOINT:
COPY ./dockerfile-dev-with-volumes/pod-transcript/my-entrypoint-transcript.sh /tmp/my-entrypoint-transcript.sh
RUN chmod 755 /tmp/my-entrypoint-transcript.sh

# Default shell to bash:
RUN ln -sf /bin/bash /bin/sh

ENTRYPOINT ["bash", "/tmp/my-entrypoint-transcript.sh"]
