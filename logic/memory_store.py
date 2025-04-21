# logic/memory_store.py

import os
import requests
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}


def init_user_memory(user_id: str, username: str):
    """Erstellt ein neues Profil, falls es nicht existiert"""
    url = f"{SUPABASE_URL}/rest/v1/user_profiles"
    payload = {
        "user_id": user_id,
        "username": username,
        "facts": [],
        "likes": [],
        "jobs": [],
        "traits": [],
        "last_updated": datetime.utcnow().isoformat()
    }
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code >= 300 and "duplicate key" not in res.text.lower():
        print("[SUPABASE] Fehler beim Erstellen des Profils:", res.text)


def get_user_memory(user_id: str):
    """Lädt das Profil (Fakten, Likes, etc.)"""
    url = f"{SUPABASE_URL}/rest/v1/user_profiles?user_id=eq.{user_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200 and res.json():
        return res.json()[0]
    return {
        "facts": [],
        "likes": [],
        "jobs": [],
        "traits": []
    }


def save_user_memory(user_id: str, username: str, fact=None, like=None, job=None, trait=None):
    """Speichert neue Daten, ohne Duplikate"""
    data = get_user_memory(user_id)

    updated_facts = data.get("facts", [])
    updated_likes = data.get("likes", [])
    updated_jobs = data.get("jobs", [])
    updated_traits = data.get("traits", [])

    updated = False

    if fact and fact not in updated_facts:
        updated_facts.append(fact)
        updated = True

    if like and like not in updated_likes:
        updated_likes.append(like)
        updated = True

    if job and job not in updated_jobs:
        updated_jobs.append(job)
        updated = True

    if trait and trait not in updated_traits:
        updated_traits.append(trait)
        updated = True

    if updated:
        url = f"{SUPABASE_URL}/rest/v1/user_profiles?user_id=eq.{user_id}"
        payload = {
            "facts": updated_facts,
            "likes": updated_likes,
            "jobs": updated_jobs,
            "traits": updated_traits,
            "last_updated": datetime.utcnow().isoformat()
        }
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code >= 300:
            print("[SUPABASE] Fehler beim Aktualisieren:", res.text)
