import os, datetime, requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}

def add_to_history(user_id, username, message, reply):
    url = f"{SUPABASE_URL}/rest/v1/conversation_memory"
    payload = {
        "user_id": user_id,
        "username": username,
        "message": message,
        "reply": reply,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code != 201:
        print("[ERROR] Supabase speichern fehlgeschlagen:", res.text)
