---
layout: default
version: 4.x
lang: fr
---

# Installation de l’autotranscription

> ⚠️ Si vous souhaitez déporter la transcription sur le serveur d’encodage, les commandes suivantes sont à effectuer sur le serveur d’encodage

---

## Utilisation de l’auto‑transcription dans Pod

Pour découper le fichier audio de Pod et faire sa transcription, nous avons besoin de Sox, il faut donc installer les deux librairies suivantes :

```bash
(django_pod4) pod@:/$ sudo apt-get install sox
(django_pod4) pod@:/$ sudo apt-get install libsox-fmt-mp3
```

Il faut également installer le module Python `ffmpeg-normalize` :

```bash
(django_pod4) pod@:/path/to/project/django_projects/podv4$ pip install ffmpeg-normalize
```

Tous les modèles peuvent être stockés dans `/path/to/project/django_projects/transcription`.
Il convient de faire un sous‑dossier par langue (ex. `fr`, `en`) et par type de modèle (`whisper`, `vosk`, etc.).

Par exemple, pour un modèle Vosk français :
`/path/to/project/django_projects/transcription/fr/vosk/vosk-model-fr-0.6-linto-2.2.0/`

À présent, vous pouvez installer un des deux modèles : **Whisper** ou **Vosk**. Il est toutefois conseillé d’utiliser Whisper.

Le modèle STT de Coqui-AI n’étant plus activement maintenu, et étant moins performant que les modèles **Whisper** ou **Vosk**, il a été retiré de Pod v4.
{: .alert .alert-warning}

---

## Vosk

Installez l’application dans l’environnement virtuel (`vosk==0.3.45`) :

```bash
(django_pod4)pod@podv4:/usr/local/django_projects/podv4$ pip3 install vosk
```

Téléchargez les modèles depuis : [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)

Par exemple, pour le modèle Français :

```bash
(django_pod4) pod@:/path/to/project/.../transcription/fr/vosk/$ wget https://alphacephei.com/vosk/models/vosk-model‑fr‑0.6‑linto‑2.2.0.zip
```

Puis décompressez :

```bash
sudo apt-get install unzip
unzip vosk-model‑fr‑0.6‑linto‑2.2.0.zip
```

Dans `custom/settings-local.py`, ajoutez :

```python
# Transcription
USE_TRANSCRIPTION = True

# Transcription use: "Whisper" ou "VOSK"
TRANSCRIPTION_TYPE = "VOSK"

# Paramétrage des modèles
TRANSCRIPTION_MODEL_PARAM = {
  'VOSK': {
    'fr': {
      'model': "/path/of/project/django_projects/transcription/fr/vosk/vosk‑model‑fr‑0.6‑linto‑2.2.0",
    }
  }
}
```

Pour l’anglais, ajoutez :

```python
'VOSK': {
  'fr': { … },
  'en': {
    'model': "/path/of/project/.../transcription/en/vosk/vosk‑model‑en‑us‑0.22",
  }
}
```

Lors de l’upload d’une vidéo avec l’auto-transcription activée, le modèle Vosk sera utilisé.

### [OPTIONNEL] Enrichissement du modèle Vosk

En installant les modèles de compilation vous pourrez contribuer à l’enrichissement des modèles.

Les modèles utilisés pour l’enrichissement du modèle peuvent être stockés dans `/path/to/project/django_projects/compile-model`

Il faut télécharger le modèle de compilation correspondant sur ce lien : [https://alphacephei.com/vosk/lm#update-process](https://alphacephei.com/vosk/lm#update-process)

Par exemple pour le modèle français :

```bash
wget https://alphacephei.com/vosk/models/vosk-model‑fr‑0.6‑linto‑2.2.0‑compile.zip
sudo apt-get install unzip
unzip vosk‑model‑fr‑0.6‑linto‑2.2.0‑compile.zip
```

La structure doit ressembler à :

```txt
compile-model
|--fr
|   |--conf
|   |   |...
|   |
|   |--data
|   |   |...
|   |
|   |--db
|   |   |...
|   |
|   |--exp
|   |   |...
|   |
|   |--local
|   |   |...
|   |
|   |--mfcc
|   |   |...
|   |
|   |--steps
|   |   |...
|   |
|   |--utils
|   |   |...
|   |
|   |--cmd.sh
|   |--compile-grapg.sh
|   |--decode.sh
|   |--dict.py
|   |--path.sh
|
|--en
```

Maintenant il faut installer docker sur votre machine. (voir [https://docs.docker.com/engine/install/debian/](https://docs.docker.com/engine/install/debian/) si besoin).

Après que docker soit installé, créer un fichier entrypoint.sh et DockerFile dans un même dossier.

Copier le script suivant dans le fichier `entrypoint.sh` :

```bash
#!/bin/bash
modelPath="$KALDI_ROOT/compile-model/$1"
cat "$KALDI_ROOT/tools/env.sh" > "$modelPath/path.sh"
cd $modelPath
/bin/bash -c "./compile-graph.sh"
/bin/bash -c "utils/build_const_arpa_lm.sh lm.gz data/lang_test data/lang_test_rescore"
```

Puis copier le code ci-dessous, fait sur mesure afin d’enrichir un modèle dans le Fichier _DockerFile_, cela créera un container avec tout ce qu’il faut installer :

```bash
## Build the DockerFile
# docker build --tag kaldi -f DockerFile .
##
## Example of manual execution of the Docker file
# sudo docker run -v ${PWD}/compile-model:/kaldi/compile-model -it kaldi
##
FROM debian:10
RUN apt-get update && apt-get install -y ca-certificates \
 && apt-get install -y \
 python3-pip \
 git \
 && apt-get install -y zlib1g-dev automake autoconf unzip wget sox gfortran libtool subversion python2.7 nano libfst-tools \
 && apt-get clean
RUN python3 --version
ENV KALDI_ROOT="/kaldi"
RUN git clone https://github.com/kaldi-asr/kaldi.git $KALDI_ROOT
WORKDIR $KALDI_ROOT"/tools"
RUN bash $KALDI_ROOT"/tools/extras/check_dependencies.sh"
RUN touch $KALDI_ROOT"/tools/python/.use_default_python"
RUN bash $KALDI_ROOT"/tools/extras/install_mkl.sh"
RUN apt-get install gfortran sox
RUN make -j $(nproc)
RUN pip3 install phonetisaurus
RUN bash $KALDI_ROOT"/tools/extras/install_opengrm.sh"
RUN make
RUN bash $KALDI_ROOT"/tools/extras/install_irstlm.sh"
RUN apt-get install gawk
RUN bash $KALDI_ROOT"/tools/extras/install_srilm.sh" "unkown" "unkown" "unkown"
RUN cd $KALDI_ROOT"/src" && ./configure --shared
RUN cd $KALDI_ROOT"/src" && make depend -j $(nproc)
RUN cd $KALDI_ROOT"/src" && make -j $(nproc)
RUN cd $KALDI_ROOT"/src/fstbin" && make
RUN echo "export PATH="$KALDI_ROOT"/src/fstbin:\$PATH" >> $KALDI_ROOT"/tools/env.sh"
RUN cd $KALDI_ROOT"/src/lmbin" && make
RUN echo "export PATH="$KALDI_ROOT"/src/lmbin:\$PATH" >> $KALDI_ROOT"/tools/env.sh"
RUN cd $KALDI_ROOT"/src/tree" && make
RUN echo "export PATH="$KALDI_ROOT"/src/tree:\$PATH" >> $KALDI_ROOT"/tools/env.sh"
RUN cd $KALDI_ROOT"/src/bin" && make
RUN echo "export PATH="$KALDI_ROOT"/src/bin:\$PATH" >> $KALDI_ROOT"/tools/env.sh"
COPY entrypoint.sh /entrypoint.sh
WORKDIR $KALDI_ROOT
ENTRYPOINT ["/entrypoint.sh"]
```

Après avoir copié et créé les deux fichiers _Dockerfile_ et entrypoint.sh il suffit de lancer la commande ci-dessous en étant dans la même dossier que les fichiers précédemment mentionnés.

```bash
docker build --tag kaldi -f DockerFile .
```

Pour finir, il faut activer l’enrichissement du modèle vosk dans une application pod, pour cela il suffit d’ajouter dans le fichier `custom/settings-local.py` les paramètres suivants :

```python
ACTIVE_ENRICH = True
MODEL_COMPILE_DIR = "/path/to/project/django_projects/compile-model"
```

---

## Whisper (v20240930)

Sur les encodeurs :

```bash
pip install openai-whisper
```

ou si vous souhaitez bénéficier des derniers commits :

```bash
pip install git+https://github.com/openai/whisper.git
```

Exemple de configuration `custom/settings_local.py` :

```python
TRANSCRIPTION_TYPE = "WHISPER"
TRANSCRIPTION_MODEL_PARAM = {
  'WHISPER': {
    'fr': {
      'model': "small",
      'download_root': "/usr/local/django_projects/transcription/whisper/",
    },
    'en': {
      'model': "small",
      'download_root': "/usr/local/django_projects/transcription/whisper/",
    }
  }
}
```

Pour créer le répertoire adéquat :

```sh
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ mkdir /usr/local/django_projects/transcription/whisper -p
```

Voir les détails ici pour le choix du modèle : [https://github.com/openai/whisper#available-models-and-languages](https://github.com/openai/whisper#available-models-and-languages)

Le modèle `small` n’est pas plus gourmand que Vosk et offre déjà de bonnes performances.

> ⚠️ Personnellement, je recommande le modèle `medium` qui est certes un peu plus gourmand mais qui offre de très bons résultats, bien mieux que Vosk.
