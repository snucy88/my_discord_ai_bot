import time
import re

# Dynamisches Relevanz-Gedächtnis pro User
relevance_memory = {}

# Standardgewichtung für Scores
DEFAULT_WEIGHTS = {
    "mention": 1.0,
    "trigger": 0.8,
    "question": 0.6,
    "topic_shift": 0.5,
    "low_confidence": -1.0,
}

# Hilfsfunktion: ist der Botname oder eine typische Frage enthalten?
def detect_trigger_patterns(content, username, botname="monday"):
    content = content.lower()
    triggers = []

    if botname in content or f"@{botname}" in content:
        triggers.append("mention")

    if any(word in content for word in ["was meinst du", "und du", "monday", "was sagst du", "deine meinung"]):
        triggers.append("trigger")

    if content.endswith("?"):
        triggers.append("question")

    return triggers

# Hauptlogik: Entscheidet, ob der Bot antworten sollte
def should_respond(message, last_messages, bot_id, botname="monday"):
    author = str(message.author.display_name)
    content = message.content.lower()
    user_id = str(message.author.id)

    if user_id not in relevance_memory:
        relevance_memory[user_id] = {
            "last_trigger_score": 0,
            "last_addressed_by": [],
            "known_triggers": [],
            "ignored_topics": [],
            "last_active": 0,
        }

    mem = relevance_memory[user_id]

    triggers = detect_trigger_patterns(content, author, botname)
    score = sum(DEFAULT_WEIGHTS.get(t, 0.5) for t in triggers)

    # Check auf neue Kontexte (Themenwechsel)
    recent_context = " ".join([m.content.lower() for m in last_messages[-5:]])
    if botname in recent_context and botname not in content:
        triggers.append("topic_shift")
        score += DEFAULT_WEIGHTS["topic_shift"]

    # Speichern was der Bot gelernt hat
    mem["last_trigger_score"] = score
    mem["last_active"] = time.time()
    if score >= 0.5:
        mem["last_addressed_by"].append(author)

    # Lernfähiger Trigger-Speicher
    for t in triggers:
        if t not in mem["known_triggers"]:
            mem["known_triggers"].append(t)

    return score >= 0.6
