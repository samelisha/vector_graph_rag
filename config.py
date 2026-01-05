import os
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

# -----------------------------
# Gmail / Email Configuration
# -----------------------------
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

IMAP_SERVER = "imap.gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# -----------------------------
# Paths & Storage
# -----------------------------
KB_DIR = "kb"                     # knowledge base files (.md, .txt etc.)
FAISS_DIR = "faiss_store"         # persistent FAISS index directory
MEMORY_DIR = "memory"             # per-sender conversation memory files

os.makedirs(KB_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)

# -----------------------------
# Models
# -----------------------------

# Local embedding model (HuggingFace)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Local LLM through Ollama
# You should pull this model with:
#   ollama pull qwen2.5:3b
OLLAMA_MODEL = "qwen2.5:3b"

# -----------------------------
# Conversation Memory Settings
# -----------------------------
# Number of previous user/assistant pairs retained per sender
MAX_MEMORY_MESSAGES = 8

# -----------------------------
# Agent Behavior
# -----------------------------
AUTO_REPLY_DISCLAIMER = (
    "⚠️ This is an auto-generated email.\n"
    "Please verify any important information before acting on it."
)