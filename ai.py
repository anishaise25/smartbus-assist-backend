"""Understands a spoken/typed command (en / kn / hi) with keywords - works without Gemini.
Member 1 can call Gemini first and use this as the fallback, or send Gemini's text through it."""
from i18n import tr

SOS = ["sos", "help", "emergency", "danger", "ಸಹಾಯ", "ಅಪಾಯ", "ತುರ್ತು", "मदद", "बचाओ", "आपातकाल", "खतरा",
       "एसओएस", "एस ओ एस", "ಎಸ್ ಒ ಎಸ್", "ಎಸ್‌ಒಎಸ್", "ಎಸ್ಒಎಸ್", "s o s"]
WHERE = ["where am i", "which stop", "ಎಲ್ಲಿದ್ದೇನೆ", "ಯಾವ ನಿಲ್ದಾಣ", "कहाँ हूँ", "कहां हूं", "कौन सा स्टॉप"]
REPEAT = ["repeat", "again", "say that", "ಮತ್ತೆ", "ಪುನಃ", "दोबारा", "फिर से"]
REMAINING = ["how many stops", "stops left", "stops remaining", "ಎಷ್ಟು ನಿಲ್ದಾಣ", "कितने स्टॉप"]
HELP = ["how to use", "what can you do", "ಹೇಗೆ ಬಳಸುವುದು", "कैसे इस्तेमाल", "कैसे उपयोग"]
BOARDED = ["boarded", "start trip", "i am on the bus", "ಹತ್ತಿದ್ದೇನೆ", "ಹತ್ತಿದೆ", "चढ़ गया", "चढ़ गई", "चढ़ गए"]


def _has(text, words):
    return any(w in text for w in words)


def find_stops(conn, text):
    """Stop ids mentioned in the text (English/Kannada/Hindi names), in order of appearance."""
    cands = [(r["id"], r["name"]) for r in conn.execute("SELECT id, name FROM stops")]
    cands += [(r["stop_id"], r["name"]) for r in conn.execute("SELECT stop_id, name FROM stop_names")]
    low = text.lower()
    taken, found = [False] * len(low), []
    for sid, name in sorted(cands, key=lambda c: -len(c[1])):      # longest names first
        n = name.lower()
        start = low.find(n)
        while start != -1:
            if not any(taken[start:start + len(n)]):
                taken[start:start + len(n)] = [True] * len(n)
                found.append((start, sid))
                break
            start = low.find(n, start + 1)
    found.sort()
    ids = []
    for _, sid in found:
        if sid not in ids:
            ids.append(sid)
    return ids


def parse_command(conn, text, lang="en"):
    low = (text or "").lower().strip()
    out = {"text": text, "lang": lang, "intent": "unknown", "source": None, "destination": None}
    if _has(low, SOS):
        out["intent"] = "sos"
    elif _has(low, WHERE):
        out["intent"] = "where_am_i"
    elif _has(low, REMAINING):
        out["intent"] = "stops_remaining"
    elif _has(low, HELP):
        out["intent"] = "help"
        out["speech"] = tr(lang, "help")
    elif _has(low, REPEAT):
        out["intent"] = "repeat"
    elif _has(low, BOARDED):
        out["intent"] = "boarded"
    else:
        ids = find_stops(conn, low)
        if ids:
            rows = [conn.execute("SELECT id, name FROM stops WHERE id=?", (i,)).fetchone() for i in ids]
            out["intent"] = "plan_route"
            out["destination"] = {"id": rows[-1]["id"], "name": rows[-1]["name"]}
            if len(rows) >= 2:
                out["source"] = {"id": rows[0]["id"], "name": rows[0]["name"]}
    if out["intent"] == "unknown":
        out["speech"] = tr(lang, "didnt_understand")
    return out
