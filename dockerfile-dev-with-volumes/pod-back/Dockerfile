#------------------------------------------------------------------------------------------------------------------------------
#  (\___/)
#  (='.'=) Dockerfile multi-stages node & python
#  (")_(")
#------------------------------------------------------------------------------------------------------------------------------
# Conteneur node
ARG NODE_VERSION
ARG PYTHON_VERSION
FROM $NODE_VERSION as source-build-js
# TODO
#FROM harbor.urba.univ-lille.fr/store/node:19 as source-build-js

WORKDIR /tmp/pod
COPY ./pod/ .
RUN yarn
#------------------------------------------------------------------------------------------------------------------------------
# Conteneur python
FROM $PYTHON_VERSION
# TODO
#FROM harbor.urba.univ-lille.fr/store/python:3.7-buster

RUN apt-get clean && apt-get update && apt-get install -y netcat

WORKDIR /usr/src/app

COPY ./requirements.txt .
COPY ./requirements-encode.txt .
COPY ./requirements-conteneur.txt .
COPY ./requirements-dev.txt .
RUN mkdir /tmp/node_modules/

COPY --from=source-build-js /tmp/pod/node_modules/ /tmp/node_modules/
# TODO remove ES version - move it into env var
RUN pip3 install --no-cache-dir -r requirements-conteneur.txt \
    && pip3 install elasticsearch==7.17.7

# ENTRYPOINT :
COPY ./dockerfile-dev-with-volumes/pod-back/my-entrypoint-back.sh /tmp/my-entrypoint-back.sh
RUN chmod 755 /tmp/my-entrypoint-back.sh

ENTRYPOINT ["bash", "/tmp/my-entrypoint-back.sh"]