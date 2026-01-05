import os
import faiss
import numpy as np
from itertools import combinations
import json

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Settings,
)

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core.node_parser import SentenceSplitter

from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore

from config import KB_DIR, FAISS_DIR, EMBEDDING_MODEL_NAME


# =========================
# Ensure dirs exist
# =========================
os.makedirs(KB_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)


print("📚 Loading knowledge base files...")
documents = SimpleDirectoryReader(KB_DIR).load_data()

print("✂️ Chunking documents...")
splitter = SentenceSplitter(chunk_size=300, chunk_overlap=30)
nodes = splitter.get_nodes_from_documents(documents)

# add file name for citation support
for n in nodes:
    n.metadata["file_name"] = n.metadata.get(
        "file_name",
        n.metadata.get("file_path", "KB Document")
    )


# =========================
# Embedding model
# =========================
print("🧠 Loading embedding model...")
Settings.embed_model = HuggingFaceEmbedding(
    model_name=EMBEDDING_MODEL_NAME
)

sample_vec = Settings.embed_model.get_text_embedding("hello world")
dim = len(sample_vec)
print(f"📏 Embedding dimension: {dim}")


# =========================
# FAISS index
# =========================
print("📦 Creating FAISS vector index...")

faiss_index = faiss.IndexFlatL2(dim)
vector_store = FaissVectorStore(faiss_index=faiss_index)

docstore = SimpleDocumentStore()
index_store = SimpleIndexStore()

storage_context = StorageContext.from_defaults(
    persist_dir=FAISS_DIR,
    vector_store=vector_store,
    docstore=docstore,
    index_store=index_store,
)

print("🧩 Building index...")
index = VectorStoreIndex.from_documents(
    nodes,
    storage_context=storage_context,
)

# persist FAISS
faiss.write_index(faiss_index, os.path.join(FAISS_DIR, "vector_store.faiss"))
docstore.persist(os.path.join(FAISS_DIR, "docstore.json"))
index_store.persist(os.path.join(FAISS_DIR, "index_store.json"))

print("📁 Vector index stored.")


# =========================
# Build semantic graph
# =========================
print("🕸️ Building semantic cross-document graph...")

def embed(text: str):
    return np.array(Settings.embed_model.get_text_embedding(text))

emb_map = {n.node_id: embed(n.text) for n in nodes}

def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

edges = []

# connect semantically related chunks, even across files
for a, b in combinations(nodes, 2):
    sim = cosine(emb_map[a.node_id], emb_map[b.node_id])

    # only keep strong relationships
    if sim >= 0.60:
        edges.append({
            "a": a.node_id,
            "b": b.node_id,
            "similarity": round(sim, 3),
            "a_file": a.metadata["file_name"],
            "b_file": b.metadata["file_name"],
        })

graph_path = os.path.join(FAISS_DIR, "semantic_graph.json")

with open(graph_path, "w") as f:
    json.dump(edges, f, indent=2)

print(f"🔗 Semantic edges created: {len(edges)}")
print("✅ Knowledge base ingestion completed successfully.")
print(f"🧩 Total chunks indexed: {len(nodes)}")
print(f"📂 Stored at: {FAISS_DIR}")