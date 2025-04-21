import discord
import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import random

from logic.prompts import build_prompt_with_memory
from logic.triggers import has_trigger
from logic.context_handler import is_followup, update_context
from logic.memory_store import init_user_memory, save_user_memory, get_user_memory
from logic.chat_log import log_chat
from logic.embedding_store import store_embedding, query_similar_messages
from logic.relevance_memory import should_respond

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

openai_client = OpenAI(api_key=OPENAI_API_KEY)
active_conversations = {}
CONVO_TIMEOUT = 600

@client.event
async def on_ready():
    print(f"{client.user} ist online – zynisch, wach und bereit.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)
    username = message.author.display_name
    content = message.content.strip()
    lowered = content.lower()

    init_user_memory(user_id, username)

    now = time.time()
    is_active, last_time = active_conversations.get(user_id, (False, 0))
    timed_out = now - last_time > CONVO_TIMEOUT

    history = [m async for m in message.channel.history(limit=10)]
    history = list(reversed(history))

    if not should_respond(message, history, client.user.id, botname="monday"):
        return

    active_conversations[user_id] = (True, now)

    like = None
    fact = None
    job = None
    trait = None

    if lowered.startswith("ich liebe") or lowered.startswith("ich mag"):
        like = lowered.split("ich liebe")[-1].strip() if "ich liebe" in lowered else lowered.split("ich mag")[-1].strip()
        if len(like.split()) > 1:
            save_user_memory(user_id, username, like=like)

    if "ich hasse" in lowered:
        hass = lowered.split("ich hasse")[-1].strip()
        if len(hass.split()) > 1:
            fact = f"hasst: {hass}"
            save_user_memory(user_id, username, fact=fact)

    if "ich arbeite" in lowered:
        job = lowered.split("ich arbeite")[-1].strip()
        if len(job.split()) > 1:
            save_user_memory(user_id, username, job=job)

    if "ich bin" in lowered:
        trait = lowered.split("ich bin")[-1].strip()
        if len(trait.split()) > 1:
            save_user_memory(user_id, username, trait=trait)

    if lowered.startswith("ich ") and len(content.split()) > 3 and not any(word in lowered for word in ["liebe", "mag", "hasse", "arbeite", "bin"]):
        quote = content.strip()
        save_user_memory(user_id, username, quote=quote)

    try:
        user_memory = get_user_memory(user_id)

        # MemoryReview mit Fehlerbehandlung bei Strings
        quotes_raw = user_memory.get("quotes", [])
        quotes = [q["value"] for q in quotes_raw if isinstance(q, dict) and q.get("score", 0) >= 0.7]
        chosen_quote = random.choice(quotes) if quotes else None

        prompt = build_prompt_with_memory(user_memory, chosen_quote=chosen_quote)
        similar = query_similar_messages(user_id, content)

        messages = [{"role": "system", "content": prompt}]
        messages += [{"role": "user", "content": m["message"]} for m in similar]
        messages.append({"role": "user", "content": content})

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        reply = response.choices[0].message.content
        await message.channel.send(reply)

        update_context(user_id)
        log_chat(user_id, username, content, reply, model_used="gpt-4")
        store_embedding(user_id, username, content)

    except Exception as e:
        await message.channel.send(f"Ich bin überfordert. Wie du. ({e})")

client.run(DISCORD_TOKEN)
