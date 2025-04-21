# logic/chat_log.py

import os
import requests
from datetime import datetime
from uuid import uuid4

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}


def log_chat(user_id: str, username: str, prompt: str, reply: str, model_used: str = "gpt-4", tokens_used: int = 0):
    """Speichert Prompt + GPT-Antwort als Gesprächseintrag"""
    url = f"{SUPABASE_URL}/rest/v1/conversation_logs"
    payload = {
        "id": str(uuid4()),
        "user_id": user_id,
        "username": username,
        "prompt": prompt,
        "reply": reply,
        "model_used": model_used,
        "tokens_used": tokens_used,
        "timestamp": datetime.utcnow().isoformat()
    }
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code >= 300:
        print("[SUPABASE] Fehler beim Speichern des Chatverlaufs:", res.text)
