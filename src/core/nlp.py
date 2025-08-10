import functools
from typing import Any, Dict

from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline

FAQ_CONTEXT = """
Powdery mildew: White powder on leaf; treatment: sulfur-based fungicide, airflow, morning irrigation.
Blight: Brown irregular spots; copper-based products, remove infected leaves.
Rust: Orange/rust pustules; remove infected tissue, use resistant cultivars.
General: Avoid excess nitrogen, reduce leaf wetness, weekly monitoring.
"""


@functools.lru_cache(maxsize=1)
def qa_pipe() -> Any:
    tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    mdl = AutoModelForQuestionAnswering.from_pretrained("distilbert-base-uncased")
    return pipeline("question-answering", model=mdl, tokenizer=tok)


def answer(question: str, context: str = FAQ_CONTEXT) -> str:
    out: Dict[str, Any] = qa_pipe()({"question": question, "context": context})
    return str(out.get("answer", ""))
