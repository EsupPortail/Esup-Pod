#------------------------------------------------------------------------------------------------------------------------------
#  (\___/)
#  (='.'=) Dockerfile python for pod-encode
#  (")_(")
#------------------------------------------------------------------------------------------------------------------------------

ARG PYTHON_VERSION=3.9

#------------------------------------------------------------------------------------------------------------------------------
# Conteneur python
FROM $PYTHON_VERSION
WORKDIR /tmp/pod
COPY ./pod/ .

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        netcat \
        ffmpeg \
    && apt-get clean\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY ./requirements-encode.txt .

RUN pip3 install --no-cache-dir -r requirements-encode.txt

# ENTRYPOINT:
COPY ./dockerfile-dev-with-volumes/pod-encode/my-entrypoint-encode.sh /tmp/my-entrypoint-encode.sh
RUN chmod 755 /tmp/my-entrypoint-encode.sh

# Default shell to bash:
RUN ln -sf /bin/bash /bin/sh

ENTRYPOINT ["bash", "/tmp/my-entrypoint-encode.sh"]
