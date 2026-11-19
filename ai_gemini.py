"""Gemini-powered command understanding (adapted from the AI teammate's ai_assistant.py).

Runs on the server so the API key never reaches the browser:
    set the environment variable GEMINI_API_KEY (Render: Environment tab).
If there is no key, Gemini is slow, or it errors, we silently fall back to the keyword parser in ai.py,
so the demo never breaks. SOS is always double-checked by keywords."""
import json
import os
from concurrent.futures import ThreadPoolExecutor

import ai
import routes_logic as rl

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
TIMEOUT_S = float(os.environ.get("GEMINI_TIMEOUT", "8"))
_pool = ThreadPoolExecutor(max_workers=2)
_client = None

PROMPT = """You are the AI assistant for SmartBus Assist, used by visually impaired bus passengers in Bengaluru.
Understand the user's request. The user may speak English, Kannada or Hindi.

Extract:
1. intent, one of: find_route, sos, where_am_i, stops_remaining, destination_alert, repeat_instruction, help
2. source: starting place exactly as spoken, or null
3. destination: ending place exactly as spoken, or null
4. language: English, Kannada, or Hindi

Return ONLY valid JSON with keys: intent, source, destination, language.
Never invent locations. If unsure, use null.

User message: {message}"""

# Gemini intent -> backend/frontend intent
INTENT_MAP = {"find_route": "plan_route", "sos": "sos", "where_am_i": "where_am_i",
              "stops_remaining": "stops_remaining", "destination_alert": "boarded",
              "repeat_instruction": "repeat", "help": "help"}


def _call_gemini(text):
    """Ask Gemini; returns a dict. Raises on any problem (caller falls back)."""
    global _client
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=key)
    result = _client.models.generate_content(model=MODEL, contents=PROMPT.replace("{message}", text))
    raw = result.text.strip()
    if raw.startswith("```"):                       # strip ```json fences
        raw = raw.strip("`").lstrip("json").strip()
    return json.loads(raw)


def _stop(conn, name):
    """Turn a place name from Gemini into a real stop in our database (or None)."""
    if not name or not str(name).strip():
        return None
    row = rl.resolve_stop(conn, name)
    if not row:
        ids = ai.find_stops(conn, str(name).lower())
        row = conn.execute("SELECT id, name FROM stops WHERE id=?", (ids[0],)).fetchone() if ids else None
    return {"id": row["id"], "name": row["name"]} if row else None


def parse(conn, text, lang="en"):
    base = ai.parse_command(conn, text, lang)       # keyword result (always available)
    if base["intent"] == "sos":                     # never let a slow/failed AI delay an emergency
        base["engine"] = "keywords"
        return base
    try:
        g = _pool.submit(_call_gemini, text).result(timeout=TIMEOUT_S)
    except Exception:
        base["engine"] = "keywords"
        return base

    intent = INTENT_MAP.get(g.get("intent"), "unknown")
    out = {"text": text, "lang": lang, "intent": intent, "source": None, "destination": None,
           "engine": "gemini", "heard_language": g.get("language")}
    if intent == "plan_route":
        out["source"], out["destination"] = _stop(conn, g.get("source")), _stop(conn, g.get("destination"))
        if not out["destination"]:                  # Gemini named a place we do not have
            if base["intent"] == "plan_route":
                base["engine"] = "keywords"
                return base
            out["intent"] = "unknown"
    if out["intent"] == "unknown":
        from i18n import tr
        out["speech"] = tr(lang, "didnt_understand")
    elif out["intent"] == "help":
        from i18n import tr
        out["speech"] = tr(lang, "help")
    return out
