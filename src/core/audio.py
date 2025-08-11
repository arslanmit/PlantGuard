"""Audio processing module for speech recognition and classification."""

import functools
from typing import Any

from transformers import pipeline
from transformers.pipelines import Pipeline


@functools.lru_cache(maxsize=1)
def asr_pipe() -> Pipeline:
    """Create and cache an automatic speech recognition pipeline."""
    # Local ASR for privacy; tiny model for speed
    return pipeline("automatic-speech-recognition", model="openai/whisper-tiny")


def transcribe(audio_path: str) -> str:
    out: dict[str, Any] = asr_pipe()(audio_path)
    return str(out.get("text", ""))


def classify_from_transcript(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["powder", "toz", "beyaz", "un"]):
        return "powdery_mildew"
    if any(k in t for k in ["brown", "spot", "leke", "yanik"]):
        return "blight"
    if any(k in t for k in ["rust", "pas", "turuncu", "püstül", "pustul"]):
        return "rust"
    return "healthy"


def transcribe_and_classify(audio_path: str) -> tuple[str, str]:
    txt = transcribe(audio_path)
    return txt, classify_from_transcript(txt)
