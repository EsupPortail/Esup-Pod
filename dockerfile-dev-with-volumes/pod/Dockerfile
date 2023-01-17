#------------------------------------------------------------------------------------------------------------------------------
#  (\___/)
#  (='.'=) Dockerfile multi-stages node & python
#  (")_(")
#------------------------------------------------------------------------------------------------------------------------------
# Conteneur node:19
FROM node:19 as source-build-js
# TODO
#FROM harbor.urba.univ-lille.fr/store/node:19 as source-build-js
WORKDIR /tmp/pod
COPY ./pod/ .
RUN yarn
#------------------------------------------------------------------------------------------------------------------------------
# Conteneur python:3.7-buster
FROM python:3.7-buster
# TODO
#FROM harbor.urba.univ-lille.fr/store/python:3.7-buster

RUN apt-get update \
    && apt-get install -y netcat \
                          ffmpeg \
                          ffmpegthumbnailer \
                          imagemagick

WORKDIR /usr/src/app

COPY ./requirements.txt .
COPY ./requirements-conteneur.txt .
RUN mkdir /tmp/node_modules/

COPY --from=source-build-js /tmp/pod/node_modules/ /tmp/node_modules/

RUN pip3 install --no-cache-dir -r requirements-conteneur.txt

# ENTRYPOINT :
COPY ./dockerfile-dev-with-volumes/pod/my-entrypoint.sh /tmp/my-entrypoint.sh
RUN chmod 755 /tmp/my-entrypoint.sh

ENTRYPOINT ["bash", "/tmp/my-entrypoint.sh"]