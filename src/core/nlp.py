"""Natural language processing module for plant care Q&A."""

import functools
from typing import Any

from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
from transformers.pipelines import Pipeline

FAQ_CONTEXT = """
Powdery mildew: White powder on leaf; treatment: sulfur-based fungicide, airflow, morning watering.
Blight: Brown irregular spots; copper-based products, remove infected leaves.
Rust: Orange/rust pustules; remove infected tissue, use resistant cultivars.
General: Avoid excess nitrogen, reduce leaf wetness, weekly monitoring.
"""


@functools.lru_cache(maxsize=1)
def qa_pipe() -> Pipeline:
    """Create and cache a question-answering pipeline."""
    # Pin to specific revision for security (latest stable as of 2024)
    model_name = "distilbert-base-uncased"
    revision = "914c22a"  # Pinned revision for security

    tok = AutoTokenizer.from_pretrained(model_name, revision=revision)  # nosec B615
    mdl = AutoModelForQuestionAnswering.from_pretrained(model_name, revision=revision)  # nosec B615
    return pipeline("question-answering", model=mdl, tokenizer=tok)


def answer(question: str, context: str = FAQ_CONTEXT) -> str:
    """Answer a question using the provided context."""
    out: dict[str, Any] = qa_pipe()({"question": question, "context": context})
    return str(out.get("answer", ""))
