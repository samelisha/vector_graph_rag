# vector_graph_rag

✉️ Email Policy Assistant — Vector + Graph RAG (Local LLM)
This project implements an automated email-based policy assistant:
reads incoming Gmail messages
understands user questions
answers using a local knowledge base
uses Vector RAG + Graph reasoning
runs entirely on local LLMs (Ollama) — no paid APIs

✅ Features
📥 Gmail IMAP listener
🤖 Automatic email replies
🧠 Local LLM (Ollama — Qwen/Mistral/etc.)
🔎 Hybrid Vector + Graph RAG retrieval
🧭 Policy-aware reasoning
🧩 Cross-document answer synthesis
🧾 Source citations
🟢 Confidence scoring
♻️ Incremental KB rebuild support
🔒 No cloud API billing required

🏗️ System Architecture
Markdown files provide structured policy KB
Chunks are embedded using SentenceTransformers
FAISS serves as vector database
Graph JSON stores policy relationships
Query flow:
email → retrieve → cluster → graph expand
        → evidence filter → answer synthesize
        → reply with confidence + sources

📂 Project Structure
.
├── kb/                         # markdown knowledge base files
├── faiss_store/                # persisted vector + graph index
├── ingest_kb.py                # builds embeddings & FAISS index
├── policy_graph_builder.py     # constructs policy graph
├── agent.py                    # core RAG + graph reasoning
├── email_listener.py           # Gmail polling + auto reply
├── mailer.py                   # SMTP sender
├── config.py                   # configuration & constants
└── requirements.txt

⚙️ Requirements
Python 3.9+
macOS / Linux recommended
Ollama installed
Gmail App Password (IMAP + SMTP)

⬇️ Install dependencies
pip install -r requirements.txt
Ensure Ollama is installed:
brew install ollama
Pull your chosen model (example Qwen 3B):
ollama pull qwen2.5:3b

🔐 Configure environment
Edit config.py:
Gmail app address & password
Ollama model name
kb folder
polling interval

🧠 Build Knowledge Base (Vector Index)
To rebuild vectors and embeddings:
rm -rf faiss_store
python ingest_kb.py

🕸️ Build Policy Graph (optional but recommended)
python policy_graph_builder.py

▶️ Start Email Agent
python email_listener.py
The agent will:
poll the inbox
detect unread messages
answer automatically

🧪 Example Queries
Try sending:
“When are invoices generated?”
“How do I delete my account?”
“If I cancel after trial, am I billed?”
“If I delete my account after being charged, can I get a refund?”
The system will:
search vector DB
expand graph neighbors
synthesize concise answer
cite sources
return confidence score

🧭 Retrieval Strategy
This implementation uses:
FAISS vector similarity search
KMeans cluster filtering
graph neighborhood expansion
answer-and-question similarity re-ranking
extractive summarization synthesis
confidence heuristic based on cosine similarity


