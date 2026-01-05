import json
import os
from config import MEMORY_DIR, MAX_MEMORY_MESSAGES

os.makedirs(MEMORY_DIR, exist_ok=True)

def _memory_path(sender):
    safe = sender.replace("@", "_at_").replace(".", "_")
    return os.path.join(MEMORY_DIR, f"{safe}.json")

def load_memory(sender):
    path = _memory_path(sender)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)["history"]

def save_memory(sender, history):
    history = history[-MAX_MEMORY_MESSAGES:]
    path = _memory_path(sender)
    with open(path, "w") as f:
        json.dump({"history": history}, f, indent=2)

