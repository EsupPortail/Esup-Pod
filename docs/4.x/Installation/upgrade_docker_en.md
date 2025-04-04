---
layout: default
version: 4.x
lang: fr
---

# Esup-Pod v4 update

## Before an update

### Announce the upgrade to users

In Pod administration (https://VOTRE_SERVEUR/admin/main/configuration/), you'll find:

The “maintenance_text_scheduled” field lets you define a customized maintenance message.
The “maintenance_scheduled” field lets you display/hide (=1 / 0) this message on Pod.

### D-Day

Switch to maintenance mode (maintenance_mode = 1), this will disable certain functions, and display a “Maintenance in progress. Some functions are unavailable”.

## Recovering sources

```sh
(django_pod4) pod@pod:~/django_projects$ git status
(django_pod4) pod@pod:~/django_projects$ git pull origin master
```

## Build stack

```sh
## Force container recompilation (mandatory on first launch or after docker-reset)
$ make docker-build
```

This will delete the following directories:

```sh
./pod/log
./pod/static
./pod/node_modules
```

## Update

Open a terminal on the _pod-back-with-volumes_ or _pod-dev-with-volumes_ container, depending on the type of installation chosen.

From this terminal, run the following commands

```sh
make upgrade
```

or the following command lines

```sh
pip3 install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
cd pod; yarn upgrade; cd ..
# Caution: before running collectstatic --clear, make sure you've backed up the static/custom folder if you've put custom files in it.
python manage.py collectstatic --no-input --clear
```

> You can run commands directly from the host machine using _docker exec_.
>
> ```sh
> docker exec -it <container_name> <command>
> Ex:
> docker exec -it pod-dev-with-volumes make upgrade
> ```
>
> Full documentation on docker exec
> <https://docs.docker.com/reference/cli/docker/container/exec/>
>

## Update settings

After updating Esup-Pod, the command below shows the new parameters compared with a previous version:

Always from the _pod-back-with-volumes_ or _pod-dev-with-volumes_ container, depending on the type of installation chosen.

```sh
python manage.py compareconfiguration *VERSION_PRECEDENTE*
```

command, for example

```sh
python manage.py compareconfiguration 3.1.1
```

will list all new parameters (and those no longer in use) from 3.1.1 to the current version.

## Optional - Updating Opencast Studio

To update the Opencast Studio in your Esup-Pod instance, follow these steps:

Go to the `opencast-studio/` folder

Retrieve the latest version of Opencast Studio with the following command:

```sh
# Select a recent tag, as the master branch is on version 2.0, which is a complete redesign.
# tags list: https://github.com/elan-ev/opencast-studio/tags
git checkout tags/2023-09-14
git pull
```

For versions up to 2023-09-14: regenerate Opencast Studio with the correct Pod configuration using the following commands:

```sh
export PUBLIC_URL=/studio
npm install
npm run build
```

For more recent versions (tags > 2023-10-10), the commands differ slightly:

```sh
export PUBLIC_PATH=/studio
npm install
npm run build:release
```

The build directory is now updated. Rename it studio, then copy it to the pod/custom/static/opencast/ directory.

```sh
mkdir -p pod/custom/static/opencast/studio
cp -r build/* pod/custom/static/opencast/studio
```

Finally, don't forget to collect your static files for production via the command:

```sh
python manage.py collectstatic
```

## Restarting the stack

From host machine

```sh
## Launch without recompiling containers or deleting directories ./pod/log, ./pod/static, ./pod/node_modules
$ make docker-stop
$ make docker-start
```
