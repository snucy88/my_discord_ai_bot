import os
import requests
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer " + SUPABASE_API_KEY,
    "Content-Type": "application/json"
}

def init_user_memory(user_id: str, username: str):
    url = f"{SUPABASE_URL}/rest/v1/user_profiles"
    payload = {
        "user_id": user_id,
        "username": username,
        "facts": [],
        "likes": [],
        "jobs": [],
        "traits": [],
        "quotes": [],
        "last_updated": datetime.utcnow().isoformat()
    }
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code >= 300 and "duplicate key" not in res.text.lower():
        print("[SUPABASE] Fehler beim Erstellen:", res.text)

def _append_memory_item(memory_list, value, score):
    for item in memory_list:
        if item["value"] == value:
            return memory_list
    memory_list.append({"value": value, "score": score})
    return memory_list

def save_user_memory(user_id: str, username: str, fact=None, like=None, job=None, trait=None, quote=None):
    url_get = f"{SUPABASE_URL}/rest/v1/user_profiles?user_id=eq.{user_id}&select=*"
    res = requests.get(url_get, headers=HEADERS)
    if res.status_code != 200 or not res.json():
        init_user_memory(user_id, username)
        res = requests.get(url_get, headers=HEADERS)

    user_data = res.json()[0]
    facts = user_data.get("facts", [])
    likes = user_data.get("likes", [])
    jobs = user_data.get("jobs", [])
    traits = user_data.get("traits", [])
    quotes = user_data.get("quotes", [])

    changed = False

    if fact:
        facts = _append_memory_item(facts, fact, score=0.9)
        changed = True
    if like:
        likes = _append_memory_item(likes, like, score=0.8)
        changed = True
    if job:
        jobs = _append_memory_item(jobs, job, score=0.7)
        changed = True
    if trait:
        traits = _append_memory_item(traits, trait, score=0.6)
        changed = True
    if quote:
        quotes = _append_memory_item(quotes, quote, score=0.9)
        changed = True

    if changed:
        url_patch = f"{SUPABASE_URL}/rest/v1/user_profiles?user_id=eq.{user_id}"
        payload = {
            "facts": facts,
            "likes": likes,
            "jobs": jobs,
            "traits": traits,
            "quotes": quotes,
            "last_updated": datetime.utcnow().isoformat()
        }
        patch_res = requests.patch(url_patch, headers=HEADERS, json=payload)
        if patch_res.status_code >= 300:
            print("[SUPABASE] Fehler beim Aktualisieren:", patch_res.text)

def get_user_memory(user_id: str):
    url = f"{SUPABASE_URL}/rest/v1/user_profiles?user_id=eq.{user_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200 and res.json():
        return res.json()[0]
    return {"facts": [], "likes": [], "jobs": [], "traits": [], "quotes": []}
