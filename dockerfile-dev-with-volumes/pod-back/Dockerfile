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

RUN apt-get update \
    && apt-get install -y --no-install-recommends netcat gettext \
    && apt-get clean\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY ./requirements.txt .
COPY ./requirements-encode.txt .
COPY ./requirements-conteneur.txt .
COPY ./requirements-dev.txt .
RUN mkdir /tmp/node_modules/

COPY --from=source-build-js /tmp/pod/node_modules/ /tmp/node_modules/
# TODO remove ES version - move it into env var
RUN pip3 install --no-cache-dir -r requirements-conteneur.txt \
    && pip3 install elasticsearch==8.17.2

# ENTRYPOINT:
COPY ./dockerfile-dev-with-volumes/pod-back/my-entrypoint-back.sh /tmp/my-entrypoint-back.sh
RUN chmod 755 /tmp/my-entrypoint-back.sh

# Default shell to bash:
RUN ln -sf /bin/bash /bin/sh

ENTRYPOINT ["bash", "/tmp/my-entrypoint-back.sh"]
