import os
import json
import re

from llama_index.llms.ollama import Ollama
from config import KB_DIR, OLLAMA_MODEL

GRAPH_PATH = "faiss_store/policy_graph.json"

# ---- instantiate Qwen2.5:3B (or your configured model) ----
llm = Ollama(
    model=OLLAMA_MODEL,
    temperature=0.0,
    options={"num_ctx": 2048}
)


def safe_json_extract(text: str):
    """
    If the model accidentally returns JSON anyway,
    try to safely extract the JSON array portion.
    """
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def parse_line_triples(text: str):
    """
    Expected preferred format:
        subject | relation | object
    """
    triples = []

    for line in text.splitlines():
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3:
                triples.append(parts)

    return triples


def extract_triples_from_text(text: str, source_file: str):
    """
    Extract triples using a Qwen-optimized prompt.
    """

    prompt = f"""
Extract subject–relation–object policy triples from the text below.

Each triple MUST be in this exact format:
subject | relation | object

Rules you must follow:
- 1 to 5 triples maximum
- relation must be 1–2 words
- use phrases that appear in the text
- DO NOT invent facts
- DO NOT explain your answer
- DO NOT add numbering
- DO NOT add bullet points
- DO NOT say anything except triples
- DO NOT return JSON
- Output ONLY triples, one per line

Text:
{text}
"""

    response = llm.complete(prompt).text.strip()

    # ---------- First attempt: pipe-delimited triples ----------
    triples = parse_line_triples(response)

    # ---------- Second attempt: JSON fallback ----------
    if not triples:
        triples = safe_json_extract(response)

    # ---------- Debug failed parses ----------
    if not triples:
        print(f"⚠️ Could not parse triples for {source_file}")
        print("🔎 Model output was:")
        print(response)
        return []

    # ---------- Normalize ----------

    cleaned = []
    for t in triples:
        if len(t) != 3:
            continue
        cleaned.append({
            "file": source_file,
            "subject": t[0].strip(),
            "relation": t[1].strip(),
            "object": t[2].strip(),
        })

    return cleaned


def chunk_text(text: str, size=900):
    """
    Simple word chunking to keep prompts short.
    """
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i:i + size])


def build_policy_graph():
    """
    Main builder: walks KB, extracts triples, writes JSON.
    """

    all_triples = []

    for fname in os.listdir(KB_DIR):
        if not fname.endswith((".md", ".txt")):
            continue

        path = os.path.join(KB_DIR, fname)

        with open(path, encoding="utf-8") as f:
            text = f.read()

        print(f"📄 Processing {fname} ...")

        for chunk in chunk_text(text):
            triples = extract_triples_from_text(chunk, fname)
            all_triples.extend(triples)

    os.makedirs("faiss_store", exist_ok=True)

    with open(GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(all_triples, f, indent=2, ensure_ascii=False)

    print(f"🕸️ Policy graph saved to {GRAPH_PATH}")
    print(f"✔ Extracted triples: {len(all_triples)}")


if __name__ == "__main__":
    build_policy_graph()
