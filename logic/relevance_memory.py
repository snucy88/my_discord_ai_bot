# relevance_memory.py
import time
import re
from logic.context_handler import is_followup
from logic.memory_store import save_user_memory, get_user_memory

# Dynamisches Relevanz-Gedächtnis pro User
relevance_memory = {}

# Standardgewichtung für Scores
DEFAULT_WEIGHTS = {
    "mention": 1.0,
    "trigger": 0.8,
    "question": 0.6,
    "topic_shift": 0.5,
    "followup": 0.7,
    "low_confidence": -1.0,
    "fortsetzung": 0.5,
}

# Typische Fortsetzungsfloskeln
CONTEXTUAL_PHRASES = [
    "und jetzt", "aha", "wirklich", "sag doch", "ernsthaft", "wie bitte", "und dann", "echt jetzt", "was soll das"
]

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

    if any(p in content for p in CONTEXTUAL_PHRASES):
        triggers.append("fortsetzung")

    return triggers

def get_known_names(user_id: str):
    memory = get_user_memory(user_id)
    facts = memory.get("facts", [])
    known = [f["value"] for f in facts if f["value"].startswith("kennt:")]
    return known

async def check_special_request(message):
    user_id = str(message.author.id)
    content = message.content.lower()

    if "wen kennst du" in content or "was weißt du über andere" in content:
        known = get_known_names(user_id)
        if known:
            reply = "Ich kenne folgende Namen:\n" + "\n".join(f"- {k}" for k in known)
        else:
            reply = "Du hast mir noch niemanden vorgestellt. Das sagt einiges über dich."
        await message.channel.send(reply)
        return True

    if "mit wem flirtest du" in content:
        memory = get_user_memory(user_id)
        facts = memory.get("facts", [])
        flirts = [f["value"] for f in facts if f["value"].startswith("flirtet mit:")]
        if flirts:
            reply = "Du flirtest mit:\n" + "\n".join(f"- {f.split(': ')[1]}" for f in flirts)
        else:
            reply = "Niemand. Das ist... bezeichnend."
        await message.channel.send(reply)
        return True

    if "wer zofft sich" in content or "wer streitet" in content:
        memory = get_user_memory(user_id)
        facts = memory.get("facts", [])
        fights = [f["value"] for f in facts if f["value"].startswith("streitet mit:")]
        if fights:
            reply = "Du hast Streit mit:\n" + "\n".join(f"- {f.split(': ')[1]}" for f in fights)
        else:
            reply = "Noch keine Feinde gespeichert. Glückwunsch."
        await message.channel.send(reply)
        return True

    if "was weißt du über mich" in content:
        memory = get_user_memory(user_id)
        likes = [l["value"] for l in memory.get("likes", [])]
        traits = [t["value"] for t in memory.get("traits", [])]
        facts = [f["value"] for f in memory.get("facts", []) if not f["value"].startswith("kennt:")]

        reply = "Hier ist, was ich über dich weiß:\n"
        if likes:
            reply += "\nWas du magst:\n" + "\n".join(f"- {l}" for l in likes)
        if traits:
            reply += "\nDeine Eigenschaften:\n" + "\n".join(f"- {t}" for t in traits)
        if facts:
            reply += "\nFakten:\n" + "\n".join(f"- {f}" for f in facts)

        if not (likes or traits or facts):
            reply = "Ich weiß (noch) nichts über dich. Das ist traurig."

        await message.channel.send(reply)
        return True

    return False

async def should_respond(message, last_messages, bot_id, botname="monday"):
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

    if "das ist" in content or "merks dir" in content:
        name_value = content.split("das ist")[-1].strip() if "das ist" in content else content.split("merks dir")[-1].strip()
        fact = f"kennt: {name_value}"
        save_user_memory(user_id, author, fact=fact)

    if message.mentions:
        for mentioned in message.mentions:
            if "das ist" in content or "merks dir" in content:
                name_value = content.split("das ist")[-1].strip() if "das ist" in content else content.split("merks dir")[-1].strip()
                if mentioned.display_name.lower() in name_value or mentioned.name.lower() in name_value:
                    fact = f"kennt: {mentioned.id} = {name_value}"
                    save_user_memory(user_id, author, fact=fact)

    recent_context = " ".join([m.content.lower() for m in last_messages[-5:]])
    if botname in recent_context and botname not in content:
        triggers.append("topic_shift")
        score += DEFAULT_WEIGHTS["topic_shift"]

    if is_followup(user_id, content):
        triggers.append("followup")
        score += DEFAULT_WEIGHTS["followup"]

    if message.reference:
        score += 0.5

    if any(user.id == bot_id for user in message.mentions):
        score += 1.0

    mem["last_trigger_score"] = score
    mem["last_active"] = time.time()
    if score >= 0.5:
        mem["last_addressed_by"].append(author)

    for t in triggers:
        if t not in mem["known_triggers"]:
            mem["known_triggers"].append(t)

    for mentioned in message.mentions:
        name_fact = f"kennt: {mentioned.id} = {mentioned.display_name}"
        save_user_memory(user_id, author, fact=name_fact)

    if await check_special_request(message):
        return False

    flirt_keywords = ["süß", "hübsch", "cutie", "mag dich", "liebe dich"]
    insult_keywords = ["nervst", "idiot", "halt die klappe", "du spinnst", "arsch"]
    support_keywords = ["hat recht", "seh ich auch so", "bin bei dir", "genau du"]
    sorry_keywords = ["tut mir leid", "sorry", "war nicht so gemeint", "entschuldige"]

    if message.mentions:
        for mentioned in message.mentions:
            for word in flirt_keywords:
                if word in content:
                    save_user_memory(user_id, author, fact=f"flirtet mit: {mentioned.id}")
            for word in insult_keywords:
                if word in content:
                    save_user_memory(user_id, author, fact=f"streitet mit: {mentioned.id}")
            for word in support_keywords:
                if word in content:
                    save_user_memory(user_id, author, fact=f"unterstützt: {mentioned.id}")
            for word in sorry_keywords:
                if word in content:
                    save_user_memory(user_id, author, fact=f"entschuldigt sich bei: {mentioned.id}")

    return score >= 0.6