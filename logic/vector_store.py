import os, json, requests
from logic.embedding import get_embedding

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}

def store_embedding(user_id, username, input_text):
    vector = get_embedding(input_text)
    payload = {
        "user_id": user_id,
        "username": username,
        "input": input_text,
        "embedding": vector
    }
    requests.post(f"{SUPABASE_URL}/rest/v1/conversation_embeddings", headers=HEADERS, data=json.dumps(payload))

def query_similar_messages(user_id, embedding, limit=3):
    payload = {
        "match_count": limit,
        "query_embedding": embedding,
        "user_id": user_id
    }
    res = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/match_messages", headers=HEADERS, json=payload)
    if res.status_code == 200:
        return res.json()
    print("[SUPABASE ERROR]", res.text)
    return []
