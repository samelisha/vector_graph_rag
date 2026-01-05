import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # optional but recommended

import re
import json
import numpy as np

from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer

from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.faiss import FaissVectorStore

from config import (
    FAISS_DIR,
    OLLAMA_MODEL
)

import faiss


# -----------------------------
# MODELS
# -----------------------------

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

Settings.embed_model = HuggingFaceEmbedding(
    model_name=EMBED_MODEL_NAME
)

Settings.llm = Ollama(
    model=OLLAMA_MODEL,
    temperature=0.2,
    options={"num_ctx": 4096},
)

cluster_model = SentenceTransformer(EMBED_MODEL_NAME)


# -----------------------------
# LOAD INDEX
# -----------------------------

def load_index():
    faiss_index = faiss.read_index(os.path.join(FAISS_DIR, "vector_store.faiss"))
    vector_store = FaissVectorStore(faiss_index=faiss_index)

    storage_context = StorageContext.from_defaults(
        persist_dir=FAISS_DIR,
        vector_store=vector_store,
    )

    return load_index_from_storage(storage_context)


index = load_index()


# -----------------------------
# HELPERS
# -----------------------------

def embed(texts):
    """Embed a list of sentences and normalize for cosine similarity."""
    embs = cluster_model.encode(texts)
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    return embs / norms


def clean_answer(text: str) -> str:
    """Remove markdown artifacts and keep 1–2 clean sentences."""

    text = re.sub(r"#+\s*", " ", text)     # remove markdown headings
    text = re.sub(r"\s+", " ", text).strip()

    sentences = re.split(r'(?<=[.!?])\s+', text)
    text = " ".join(sentences[:2]).strip()

    return text


# -----------------------------
# CORE PIPELINE
# -----------------------------

def retrieve(question, k=12):
    retriever = index.as_retriever(similarity_top_k=k)
    return retriever.retrieve(question)


def cluster_chunks(question, hits):

    texts = [h.node.text for h in hits]
    if len(texts) == 0:
        return hits

    # embed chunks & question
    chunk_vecs = embed(texts)
    q_vec = embed([question])[0]

    # choose number of clusters
    if len(texts) >= 8:
        k = 3
    elif len(texts) >= 4:
        k = 2
    else:
        return hits

    kmeans = KMeans(n_clusters=k, n_init="auto", random_state=42)
    labels = kmeans.fit_predict(chunk_vecs)

    # similarity of question to each cluster centroid
    cluster_scores = []
    for cid in range(k):
        members = chunk_vecs[labels == cid]
        centroid = np.mean(members, axis=0)
        sim = float(np.dot(centroid, q_vec))
        cluster_scores.append((sim, cid))

    # pick top two clusters
    cluster_scores.sort(reverse=True)
    chosen = {cid for _, cid in cluster_scores[:2]}

    filtered = []
    for label, h in zip(labels, hits):
        if label in chosen:
            filtered.append(h)

    return filtered if filtered else hits


def synthesize(question, hits):
    """LLM answer synthesis + refined source citation."""

    if not hits:
        return {
            "answer": "The requested information is not available in the knowledge base.",
            "confidence": "Very Low",
            "sources": [],
        }

    kb_content = "\n\n".join(h.node.text for h in hits)

    prompt = f"""
Answer the user question strictly based on the provided policy text.

Question:
{question}

Policy text:
{kb_content}

Rules:
- Answer ONLY from the policy text
- Do NOT invent rules
- Prefer short direct answers
- If refund depends on cancellation, mention both
- If answer is not clearly stated, say so

Respond with 2–3 concise sentences.
"""

    raw = Settings.llm.complete(prompt)
    answer = clean_answer(str(raw))

    # confidence heuristic based on retriever similarity
    sims = [h.score for h in hits if hasattr(h, "score")]
    avg_sim = float(np.mean(sims)) if sims else 0.0

    confidence = (
        "High" if avg_sim > 0.70 else
        "Medium" if avg_sim > 0.50 else
        "Low"
    )

    # -----------------------------
    # refined citation selection
    # -----------------------------

    q_vec = embed([question])[0]
    a_vec = embed([answer])[0]

    ranked_sources = []

    for h in hits:
        text = h.node.text
        src = (h.node.metadata or {}).get("file_name", "Unknown")

        c_vec = embed([text])[0]

        # similarity to question & answer
        sim_q = float(np.dot(c_vec, q_vec))
        sim_a = float(np.dot(c_vec, a_vec))

        # joint relevance score
        score = 0.6 * sim_q + 0.4 * sim_a

        ranked_sources.append((score, src))

    ranked_sources.sort(reverse=True)

    # keep top 3 distinct sources
    seen = set()
    sources = []
    for score, src in ranked_sources:
        if src not in seen:
            seen.add(src)
            sources.append(src)
        if len(sources) >= 3:
            break

    return {
        "answer": answer,
        "confidence": confidence,
        "sources": sources,
    }


# -----------------------------
# PUBLIC ENTRYPOINT
# -----------------------------

def handle_question(sender, question: str) -> str:

    hits = retrieve(question, k=10)
    clustered = cluster_chunks(question, hits)
    response = synthesize(question, clustered)

    final = f"""
This is an auto-generated email.
Please verify any important information before acting on it.

Answer:
{response['answer']}

Confidence: {response['confidence']}

Sources:
- """ + "\n- ".join(response["sources"]) + "\n"

    return final.strip()


# -----------------------------
# LOCAL TEST
# -----------------------------

if __name__ == "__main__":
    q = "If I delete my account after being charged, can I still receive a refund?"
    print(handle_question("test@example.com", q))
