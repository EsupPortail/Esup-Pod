"""
Esup-Pod - Completion celery tasks.
"""

import logging
import os
import shutil
import subprocess

try:
    import webvtt
except ImportError:
    webvtt = None
from celery import shared_task
from src.apps.completion.models import EnrichModelQueue
from src.apps.completion.conf import completion_settings

logger = logging.getLogger(__name__)


@shared_task
def process_enrich_model_queue():  # noqa: C901
    """
    Process pending EnrichModelQueue tasks.
    Extracts text from the Subtitle file and compiles Kaldi/VOSK models.
    """
    if not completion_settings.active_model_enrich:
        logger.debug("Model enrichment is disabled.")
        return

    queue_item = EnrichModelQueue.objects.filter(status="pending").first()
    if not queue_item:
        logger.debug("No pending EnrichModelQueue found.")
        return

    # Mark as processing
    queue_item.status = "processing"
    queue_item.save()

    try:
        track = queue_item.track
        lang = track.language
        model_type = completion_settings.transcription_type
        model_compile_dir = completion_settings.model_compile_dir

        if not model_compile_dir:
            raise ValueError("MODEL_COMPILE_DIR is not configured.")

        # Extract text from VTT
        text = ""
        try:
            if webvtt is None:
                raise ImportError(
                    "webvtt-py is required for model enrichment. Please install it."
                )
            for caption in webvtt.read(track.file.path):
                text += caption.text + "\n"
        except Exception as e:
            raise Exception(f"Failed to read VTT file: {e}")

        # 1. Write text into kaldi file
        extra_txt_path = os.path.join(model_compile_dir, lang, "db", "extra.txt")
        os.makedirs(os.path.dirname(extra_txt_path), exist_ok=True)
        with open(extra_txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        # 2. Compile model via subprocess (docker)
        subprocess.run(
            [
                "docker",
                "run",
                "-v",
                f"{model_compile_dir}:/kaldi/compile-model",
                "-it",
                "kaldi",
                lang,
            ],
            check=True,
        )

        # 3. Copy results
        params = completion_settings.transcription_model_param
        if model_type in params and lang in params[model_type]:
            dest_model_path = params[model_type][lang].get("model")
            if dest_model_path:
                from_path_graph = os.path.join(
                    model_compile_dir, lang, "exp", "chain", "tdnn", "graph"
                )
                to_path_graph = os.path.join(dest_model_path, "graph")
                if os.path.exists(to_path_graph):
                    shutil.rmtree(to_path_graph)
                if os.path.exists(from_path_graph):
                    shutil.copytree(from_path_graph, to_path_graph)

                from_path_rescore = os.path.join(
                    model_compile_dir, lang, "data", "lang_test_rescore"
                )
                to_path_rescore = os.path.join(dest_model_path, "rescore")
                os.makedirs(to_path_rescore, exist_ok=True)
                if os.path.isfile(
                    os.path.join(from_path_rescore, "G.fst")
                ) and os.path.isfile(os.path.join(from_path_rescore, "G.carpa")):
                    shutil.copy(os.path.join(from_path_rescore, "G.fst"), to_path_rescore)
                    shutil.copy(
                        os.path.join(from_path_rescore, "G.carpa"), to_path_rescore
                    )

                from_path_rnnlm = os.path.join(
                    model_compile_dir, lang, "exp", "rnnlm_out"
                )
                to_path_rnnlm = os.path.join(dest_model_path, "rnnlm")
                if os.path.exists(from_path_rnnlm):
                    os.makedirs(to_path_rnnlm, exist_ok=True)
                    shutil.copy(from_path_rnnlm, to_path_rnnlm)

        # Mark as done
        queue_item.status = "done"
        queue_item.save()

        # Trigger the next one if any
        process_enrich_model_queue.delay()

    except Exception as e:
        logger.error(f"Error processing EnrichModelQueue {queue_item.id}: {e}")
        queue_item.status = "error"
        queue_item.save()
