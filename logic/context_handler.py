import time

last_user_id = None
last_interaction_timestamp = 0
CONVERSATION_TIMEOUT = 180

FOLLOWUP_CUES = ["warum", "meinst du", "was meinst du", "findest du", "bist du", "du", "dein", "antwort", "wirklich"]

def update_context(user_id):
    global last_user_id, last_interaction_timestamp
    last_user_id = user_id
    last_interaction_timestamp = time.time()

def is_followup(user_id, content):
    now = time.time()
    if user_id == last_user_id and (now - last_interaction_timestamp) < CONVERSATION_TIMEOUT:
        return any(cue in content.lower() for cue in FOLLOWUP_CUES)
    return False
