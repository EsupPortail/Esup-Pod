---
layout: default
version: 4.x
lang: en
---

# Auto-Transcription installation

> ⚠️ If you want to offload the transcription to the encoding server, the following commands should be executed on the encoding server.

---

## Using Auto-Transcription in Pod

To split the audio file from Pod and transcribe it, we need Sox. Therefore, you need to install the following two libraries:

```bash
(django_pod4) pod@:/$ sudo apt-get install sox
(django_pod4) pod@:/$ sudo apt-get install libsox-fmt-mp3
```

You also need to install the Python module `ffmpeg-normalize`:

```bash
(django_pod4) pod@:/path/to/project/django_projects/podv4$ pip install ffmpeg-normalize
```

All models can be stored in `/path/to/project/django_projects/transcription`.
You should create a sub-folder for each language (e.g., `fr`, `en`) and for each type of model (`whisper`, `vosk`, etc.).

For example, for a French Vosk model:
`/path/to/project/django_projects/transcription/fr/vosk/vosk-model-fr-0.6-linto-2.2.0/`

Now, you can install one of the two models: **Whisper** or **Vosk**. However, it is recommended to use Whisper.

The Coqui-AI STT model is no longer actively maintained, and as it performs less well than the **Whisper** or **Vosk** models, it has been removed from Pod v4.
{: .alert .alert-warning}

---

## Vosk

Install the application in the virtual environment (`vosk==0.3.45`):

```bash
(django_pod4) pod@podv4:/usr/local/django_projects/podv4$ pip3 install vosk
```

Download the models from: [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)

For example, for the French model:

```bash
(django_pod4) pod@:/path/to/project/.../transcription/fr/vosk/$ wget https://alphacephei.com/vosk/models/vosk-model-fr-0.6-linto-2.2.0.zip
```

Then unzip:

```bash
sudo apt-get install unzip
unzip vosk-model-fr-0.6-linto-2.2.0.zip
```

In `custom/settings-local.py`, add:

```python
# Transcription
USE_TRANSCRIPTION = True

# Transcription use: "Whisper" or "VOSK"
TRANSCRIPTION_TYPE = "VOSK"

# Model settings
TRANSCRIPTION_MODEL_PARAM = {
  'VOSK': {
    'fr': {
      'model': "/path/of/project/django_projects/transcription/fr/vosk/vosk-model-fr-0.6-linto-2.2.0",
    }
  }
}
```

For English, add:

```python
'VOSK': {
  'fr': { ... },
  'en': {
    'model': "/path/of/project/.../transcription/en/vosk/vosk-model-en-us-0.22",
  }
}
```

When uploading a video with auto-transcription enabled, the Vosk model will be used.

### [OPTIONAL] Enriching the Vosk Model

By installing the compilation models, you can contribute to the enrichment of the models.

The models used for enriching the model can be stored in `/path/to/project/django_projects/compile-model`.

You need to download the corresponding compilation model from this link: [https://alphacephei.com/vosk/lm#update-process](https://alphacephei.com/vosk/lm#update-process)

For example, for the French model:

```bash
wget https://alphacephei.com/vosk/models/vosk-model-fr-0.6-linto-2.2.0-compile.zip
sudo apt-get install unzip
unzip vosk-model-fr-0.6-linto-2.2.0-compile.zip
```

The structure should look like this:

```txt
compile-model
|--fr
| |--conf
| | |...
| |
| |--data
| | |...
| |
| |--db
| | |...
| |
| |--exp
| | |...
| |
| |--local
| | |...
| |
| |--mfcc
| | |...
| |
| |--steps
| | |...
| |
| |--utils
| | |...
| |
| |--cmd.sh
| |--compile-grapg.sh
| |--decode.sh
| |--dict.py
| |--path.sh
|
|--en
```

Now you need to install Docker on your machine. (See [https://docs.docker.com/engine/install/debian/](https://docs.docker.com/engine/install/debian/) if needed).

After Docker is installed, create an `entrypoint.sh` file and a `Dockerfile` in the same directory.

Copy the following script into the `entrypoint.sh` file:

```bash
#!/bin/bash
modelPath="$KALDI_ROOT/compile-model/$1"
cat "$KALDI_ROOT/tools/env.sh" > "$modelPath/path.sh"
cd $modelPath
/bin/bash -c "./compile-graph.sh"
/bin/bash -c "utils/build_const_arpa_lm.sh lm.gz data/lang_test data/lang_test_rescore"
```

Then copy the code below, tailored to enrich a model, into the `Dockerfile` file. This will create a container with everything needed installed:

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
RUN bash $KALDI_ROOT"/tools/extras/install_srilm.sh" "unknown" "unknown" "unknown"
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

After copying and creating the two files `Dockerfile` and `entrypoint.sh`, you just need to run the following command in the same directory as the previously mentioned files:

```bash
docker build --tag kaldi -f DockerFile .
```

Finally, you need to enable the enrichment of the Vosk model in a Pod application. To do this, add the following parameters to the `custom/settings-local.py` file:

```python
ACTIVE_ENRICH = True
MODEL_COMPILE_DIR = "/path/to/project/django_projects/compile-model"
```

---

## Whisper (v20240930)

On the encoders:

```bash
pip install openai-whisper
```

Or if you want to benefit from the latest commits:

```bash
pip install git+https://github.com/openai/whisper.git
```

Example configuration for `custom/settings_local.py`:

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

To create the appropriate directory:

```sh
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ mkdir /usr/local/django_projects/transcription/whisper -p
```

See the details here for model selection: [https://github.com/openai/whisper#available-models-and-languages](https://github.com/openai/whisper#available-models-and-languages)

The `small` model is no more resource-intensive than Vosk and already offers good performance.

> ⚠️ Personally, I recommend the `medium` model, which is indeed a bit more resource-intensive but offers very good results, much better than Vosk.
