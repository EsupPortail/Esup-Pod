# Installation of ElasticSearch on Debian

https://www.elastic.co/guide/en/elasticsearch/reference/current/deb.html

## Installation of ICU Analysis

```sh
$>root@Pod:/usr/share/elasticsearch# bin/elasticsearch-plugin install analysis-icu
````

## Configuration

```sh
$>root@Pod:/etc/elasticsearch# vim elasticsearch.yml
 - cluster.name: pod-application
 - node.name: pod-1
 - discovery.zen.ping.unicast.hosts: ["elasticsearch.localhost"]
```

## To create pod index

```sh
(django_pod) pod@Pod:~/django_projects/podv3$ python manage.py create_pod_index
```

## To delete pod index

```sh
$>curl -XDELETE elasticsearch.localhost:9200/pod
```
