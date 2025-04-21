# logic/embedding_store.py

import os
import requests
from datetime import datetime
from uuid import uuid4
from logic.embedding import get_embedding  # ← nutzt dein embedding.py

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}


def store_embedding(user_id: str, username: str, input_text: str):
    """Speichert ein Vektor-Embedding in Supabase"""
    vector = get_embedding(input_text)

    payload = {
        "id": str(uuid4()),
        "user_id": user_id,
        "username": username,
        "input": input_text,
        "embedding": vector,
        "created_at": datetime.utcnow().isoformat()
    }

    url = f"{SUPABASE_URL}/rest/v1/conversation_embeddings"
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code >= 300:
        print("[SUPABASE] Fehler beim Speichern des Embeddings:", res.text)


def query_similar_messages(user_id: str, input_text: str, limit: int = 3):
    """Fragt semantisch ähnliche alte Aussagen des Users ab"""
    vector = get_embedding(input_text)
    payload = {
        "user_id": user_id,
        "query_embedding": vector,
        "match_count": limit
    }

    url = f"{SUPABASE_URL}/rest/v1/rpc/match_messages"
    res = requests.post(url, headers=HEADERS, json=payload)

    if res.status_code == 200:
        return res.json()
    else:
        print("[SUPABASE] Fehler bei Vektor-Suche:", res.text)
        return []
