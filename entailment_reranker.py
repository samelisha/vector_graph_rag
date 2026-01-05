from llama_index.llms.ollama import Ollama
from config import OLLAMA_MODEL

llm = Ollama(
    model=OLLAMA_MODEL,
    temperature=0.0,
    options={"num_ctx": 2048}
)

def score_entailment(question: str, text: str):
    """
    Return label + confidence:
    - supports
    - contradicts
    - irrelevant
    """

    prompt = f"""
Determine whether the document text supports the user question.

Respond JSON:
{{
 "label": "supports" | "contradicts" | "irrelevant",
 "confidence": 0.0–1.0
}}

Question:
{question}

Text:
{text}
"""

    resp = llm.complete(prompt).text.strip()

    try:
        return eval(resp)
    except Exception:
        return {"label": "irrelevant", "confidence": 0.0}
