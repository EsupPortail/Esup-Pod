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

RUN apt-get clean && apt-get update && apt-get install -y netcat

WORKDIR /usr/src/app

COPY ./requirements.txt .
COPY ./requirements-conteneur.txt .
COPY ./requirements-encode.txt .
COPY ./requirements-dev.txt .

RUN pip3 install --no-cache-dir -r requirements-dev.txt \
    && pip3 install elasticsearch==7.17.9

# ENTRYPOINT :
COPY ./dockerfile-dev-with-volumes/pod-activitypub/my-entrypoint-activitypub.sh /tmp/my-entrypoint-activitypub.sh
RUN chmod 755 /tmp/my-entrypoint-activitypub.sh

ENTRYPOINT ["bash", "/tmp/my-entrypoint-activitypub.sh"]
