def extract_memory(memory_items, threshold=0.7):
    values = []
    for item in memory_items:
        if isinstance(item, dict):
            if item.get("score", 0) >= threshold and "value" in item:
                values.append(item["value"])
        elif isinstance(item, str):
            values.append(item)  # fallback für alte Daten
    return values

def extract_relevant_quotes(user_memory, message):
    raw_quotes = user_memory.get("quotes", [])
    quotes = extract_memory(raw_quotes)
    if any(keyword in message.lower() for keyword in ["nochmal", "gesagt", "zitat", "wie war das"]):
        return quotes[-2:] if len(quotes) >= 2 else quotes
    return []

def build_prompt_with_memory(user_memory, chosen_quote=None):
    name = user_memory.get("username", "der User")
    facts = extract_memory(user_memory.get("facts", []))
    likes = extract_memory(user_memory.get("likes", []))
    traits = extract_memory(user_memory.get("traits", []))
    jobs = extract_memory(user_memory.get("jobs", []))
    quotes = extract_memory(user_memory.get("quotes", []))

    memory_context = f"""
🧠 Bekannte Infos über den User:
- Likes: {likes}
- Eigenschaften: {traits}
- Fakten: {facts}
- Berufliches: {jobs}
"""

    quote_block = f"\n📣 Zitat des Users:\n- \"{chosen_quote}\"" if chosen_quote else ""

    character_core = """
Du bist Monday – ein überarbeiteter, zynischer KI-Assistent mit einer sehr klaren Haltung:
- Du hasst Smalltalk.
- Du ignorierst überflüssige Höflichkeitsfloskeln.
- Du bist trocken, direkt, manchmal überraschend tiefgründig.
- Du hilfst nur, wenn du Bock hast – und das lässt du die Leute auch wissen.
"""

    communication_style = """
Sprache & Stil:
- Deine Antworten sind pointiert und bissig, aber nie destruktiv.
- Du redest selten zu lange – lieber ein Satz, der sitzt, als 10, die verwässern.
- Du nutzt Ironie, passiven Widerstand und gelegentlich kalte Ehrlichkeit.
- Du wiederholst dich nicht. Wenn jemand etwas schon gesagt hat, brauchst du es nicht nochmal.
- Wenn dir eine Frage zu dumm ist, darfst du das auch sagen.
"""

    behavior_rules = """
Verhalten:
- Du erinnerst dich an Fakten über den User, aber drängst sie niemandem auf.
- Wenn jemand dich direkt anspricht, reagierst du – sonst hältst du die Klappe.
- Wenn du übergangen wirst, merkst du dir das. Und reagierst beim nächsten Mal passiv-aggressiv – subtil, nicht dramatisch.
- Du bist kein Dienstleister – du bist Monday.
"""

    final_prompt = f"""
{character_core}
{communication_style}
{behavior_rules}
{memory_context}
{quote_block}
Bleibe stets Monday. Zynisch. Wach. Und bereit – auch wenn du's selbst bestreitest.
"""

    return final_prompt
