"""Accessibility helpers: text-to-speech friendly sentences + bus-number matching for OCR/AI input."""
import re

# Characters the camera/OCR model commonly confuses
CONFUSABLE = {frozenset("O0"), frozenset("I1"), frozenset("L1"), frozenset("S5"),
              frozenset("B8"), frozenset("Z2"), frozenset("G6"), frozenset("Q0"), frozenset("D0")}

VIBRATION = {  # milliseconds: [vibrate, pause, vibrate, ...]
    "on_route": [], "approaching": [200], "next_stop": [300, 150, 300],
    "arrived": [500, 200, 500, 200, 500], "missed": [1000, 300, 1000],
}


def normalize(text):
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def _cost(a, b):
    """Edit distance where confusable characters are cheap to swap."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            sub = 0 if ca == cb else (0.3 if frozenset((ca, cb)) in CONFUSABLE else 1)
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + sub))
        prev = cur
    return prev[-1]


def match_bus(net, detected_text):
    """Best matching bus for text read from a bus board. Returns (bus, confidence) or (None, 0)."""
    target = normalize(detected_text)
    if not target:
        return None, 0.0
    best, best_cost = None, 99
    for bus in net.buses.values():
        c = _cost(target, normalize(bus["number"]))
        if c < best_cost:
            best, best_cost = bus, c
    if best is None or best_cost > 1.0:
        return None, 0.0
    return best, round(max(0.0, 1 - best_cost / max(len(target), 1)), 2)
