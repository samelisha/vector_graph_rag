import os

KB_DIR = "kb"

def get_kb_last_modified() -> float:
    latest = 0.0
    for root, _, files in os.walk(KB_DIR):
        for f in files:
            latest = max(latest, os.path.getmtime(os.path.join(root, f)))
    return latest