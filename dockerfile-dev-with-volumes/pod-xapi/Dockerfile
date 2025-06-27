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

WORKDIR /usr/src/app

COPY ./requirements-encode.txt ./requirements-conteneur.txt .

RUN pip3 install --no-cache-dir \
    --requirement requirements-encode.txt \
    --requirement requirements-conteneur.txt

# ENTRYPOINT:
COPY ./dockerfile-dev-with-volumes/pod-xapi/my-entrypoint-xapi.sh /tmp/my-entrypoint-xapi.sh
RUN chmod 755 /tmp/my-entrypoint-xapi.sh

# Default shell to bash:
RUN ln -sf /bin/bash /bin/sh

ENTRYPOINT ["bash", "/tmp/my-entrypoint-xapi.sh"]
