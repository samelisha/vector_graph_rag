from llama_index.llms.ollama import Ollama
from config import OLLAMA_MODEL

llm = Ollama(
    model=OLLAMA_MODEL,
    temperature=0.1,
    options={"num_ctx": 2048}
)

def decompose_query(question: str) -> list[str]:

    prompt = f"""
Decompose the user question into simpler policy questions.

Rules:
- produce 2–5 atomic questions
- preserve meaning exactly
- do not assume missing facts
- do not answer
- one question per line

User question:
{question}
"""

    resp = llm.complete(prompt).text.strip()

    parts = [l.strip() for l in resp.split("\n") if len(l.strip()) > 5]
    return parts[:5]
