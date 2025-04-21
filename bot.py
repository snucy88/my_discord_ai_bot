import discord
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

from logic.prompts import PROMPT
from logic.triggers import has_trigger
from logic.context_handler import is_followup, update_context
from logic.memory_store import init_user_memory, save_user_memory
from logic.chat_log import log_chat
from logic.embedding_store import store_embedding, query_similar_messages

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

openai_client = OpenAI(api_key=OPENAI_API_KEY)
active_conversations = {}
CONVO_TIMEOUT = 600  # 10 Min Timeout für Follow-ups

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

    # User initialisieren
    init_user_memory(user_id, username)

    # User-Memory speichern anhand typischer Phrasen
    if "ich liebe" in lowered or "ich mag" in lowered:
        like = lowered.split("ich liebe")[-1].strip() if "ich liebe" in lowered else lowered.split("ich mag")[-1].strip()
        save_user_memory(user_id, username, like=like)

    if "ich hasse" in lowered:
        hass = lowered.split("ich hasse")[-1].strip()
        save_user_memory(user_id, username, fact=f"hasst: {hass}")

    if "ich arbeite" in lowered:
        job = lowered.split("ich arbeite")[-1].strip()
        save_user_memory(user_id, username, job=job)

    if "ich bin" in lowered:
        trait = lowered.split("ich bin")[-1].strip()
        save_user_memory(user_id, username, trait=trait)

    # Kontext bestimmen
    now = time.time()
    is_active, last_time = active_conversations.get(user_id, (False, 0))
    timed_out = now - last_time > CONVO_TIMEOUT
    mentioned = client.user.mentioned_in(message) or "monday" in lowered

    should_respond = (
        mentioned or has_trigger(lowered) or is_followup(user_id, lowered) or (is_active and not timed_out)
    )

    if should_respond:
        active_conversations[user_id] = (True, now)

        try:
            # Ähnliche Kontexte laden (Vektor-Suche)
            similar = query_similar_messages(user_id, content)

            # GPT-Kontext aufbauen
            messages = [{"role": "system", "content": PROMPT}]
            messages += [{"role": "user", "content": m["message"]} for m in similar]
            messages.append({"role": "user", "content": content})

            # GPT antworten lassen
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            reply = response.choices[0].message.content
            await message.channel.send(reply)

            # Kontext, Verlauf und Embedding speichern
            update_context(user_id)
            log_chat(user_id, username, content, reply, model_used="gpt-4")
            store_embedding(user_id, username, content)

        except Exception as e:
            await message.channel.send(f"Ich bin verwirrt. Wie du. ({e})")

client.run(DISCORD_TOKEN)
