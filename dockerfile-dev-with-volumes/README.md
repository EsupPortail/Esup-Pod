$ docker-compose -f ./docker-compose-portainer-with-volumes.yml -p portainer up --build 
$ docker-compose -f ./docker-compose-portainer-with-volumes.yml -p portainer down -v
$ docker-compose -f ./docker-compose-dev-with-volumes.yml -p esup-pod up --build 
$ docker-compose -f ./docker-compose-dev-with-volumes.yml -p esup-pod down -v
$ KO : docker run --rm -it -v ${PWD}:/usr/src/app --entrypoint bash python:3
$ KO : docker run --rm -it -v ${PWD}:/usr/src/app --entrypoint sh python:3.7.15-alpine3.16 
$ OK : docker run --rm -it -v ${PWD}:/usr/src/app --entrypoint bash python:3.7-buster
$ OK : docker run --rm -it -v ${PWD}:/tmp --entrypoint bash node:19
$ OK : docker run --rm -it --entrypoint bash elasticsearch:7.17.7
$ pip show webrtcvad
$ ls -ltrah /usr/local/lib/python3.7/site-packages/
$ apt update && apt install netcat  telnet vim -y
$ until nc -z elasticsearch 9200; do echo waiting for elasticsearch; sleep 2; done;
$ telnet elasticsearch 9200; do echo waiting for elasticsearch; sleep 2; done;
$ curl -XGET "elasticsearch:9200/pod/_search"

https://www.esup-portail.org/wiki/display/ES/Installation+de+la+plateforme+Pod+V3
https://github.com/EsupPortail/pod
https://hub.docker.com/_/debian/tags?page=2
https://forums.docker.com/t/git-clone-command-fails-with-timeout/100655