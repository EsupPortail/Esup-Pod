#------------------------------------------------------------------------------------------------------------------------------
#  (\___/)
#  (='.'=) Dockerfile multi-stages node & python
#  (")_(")
#------------------------------------------------------------------------------------------------------------------------------
# Conteneur node
ARG NODE_VERSION=23
ARG PYTHON_VERSION=3.9
FROM $NODE_VERSION AS source-build-js

WORKDIR /tmp/pod
COPY ./pod/ .
RUN yarn
#------------------------------------------------------------------------------------------------------------------------------
# Conteneur python
FROM $PYTHON_VERSION
# TODO
#FROM harbor.urba.univ-lille.fr/store/python:3.7-buster

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        gettext \
        curl \
    && apt-get clean\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY ./requirements.txt ./requirements-conteneur.txt ./requirements-encode.txt ./requirements-dev.txt ./
RUN mkdir /tmp/node_modules/

COPY --from=source-build-js /tmp/pod/node_modules/ /tmp/node_modules/

RUN pip3 install --no-cache-dir \
    --requirement requirements-dev.txt \
    --requirement requirements-conteneur.txt \
    && pip3 install elasticsearch==8.17.2

# ENTRYPOINT:
COPY ./dockerfile-dev-with-volumes/pod/my-entrypoint.sh /tmp/my-entrypoint.sh
RUN chmod 755 /tmp/my-entrypoint.sh

# Default shell to bash:
RUN ln -sf /bin/bash /bin/sh

HEALTHCHECK --timeout=3s --start-period=60s --start-interval=1s CMD \
    curl --fail http://pod.localhost:8000 || exit 1

ENTRYPOINT ["bash", "/tmp/my-entrypoint.sh"]
