"""Presentation demo: a visually impaired passenger's journey, end to end.
    python demo.py              # English
    python demo.py --lang kn    # Kannada     (or hi for Hindi)
Runs against a temporary database, so it never touches your real data."""
import argparse
import os
import tempfile

from app import create_app

ap = argparse.ArgumentParser()
ap.add_argument("--lang", default="en", choices=["en", "kn", "hi"])
L = ap.parse_args().lang
c = create_app(os.path.join(tempfile.mkdtemp(), "demo.db")).test_client()


def step(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def say(r, note=""):
    d = r.get_json()
    print(f'  SPEAKER : "{d["speech"]}"')
    if d.get("vibration"):
        print(f"  HAPTIC  : {d['vibration']} ms   {note}")
    return d


step("SCENARIO 1  Planning: 'I want to go from Majestic to Whitefield'")
print("  User says the destination by voice; app calls /api/search")
say(c.get(f"/api/search?from=Majestic&to=Whitefield&lang={L}"))

step("SCENARIO 2  No direct bus: Banashankari to Whitefield (bus change needed)")
d = c.get(f"/api/search?from=Banashankari&to=Whitefield&lang={L}").get_json()
print(f'  SPEAKER : "{d["speech"]}"')
print(f"  Alternatives found: {len(d['direct_buses']) + len(d['transfer_routes'])}")

step("SCENARIO 3  At the bus stop: camera reads a bus board")
print("  3a. Correct bus (camera read '335 E', destination Whitefield)")
say(c.post("/api/assist/identify-bus", json={"detected_text": "335 E", "destination": "Whitefield",
                                            "lat": 12.9767, "lng": 77.5713, "lang": L}))
print("\n  3b. Wrong bus (camera read '201', user wants Whitefield)")
say(c.post("/api/assist/identify-bus", json={"detected_text": "201", "destination": "Whitefield",
                                            "lat": 12.9767, "lng": 77.5713, "lang": L}))
print("\n  3c. Blurry image (OCR confuses O and 0: '5OOD')")
say(c.post("/api/assist/identify-bus", json={"detected_text": "5OOD", "lang": L}))
print("\n  3d. Unreadable image")
say(c.post("/api/assist/identify-bus", json={"detected_text": "??", "lang": L}))

step("SCENARIO 4  On the bus: live GPS alerts (Majestic -> Marathahalli on 335E)")
t = c.post("/api/trips", json={"bus_number": "335E", "boarding_stop": "Majestic",
                               "destination": "Marathahalli"}).get_json()["trip_id"]
fixes = [("Departing Majestic", 12.9767, 77.5713), ("Passing Indiranagar", 12.9784, 77.6408),
         ("Passing Domlur", 12.9609, 77.6387), ("Reached destination", 12.9569, 77.7011)]
for label, lat, lng in fixes:
    print(f"\n  GPS fix: {label}")
    say(c.post(f"/api/trips/{t}/location", json={"lat": lat, "lng": lng, "lang": L}))

step("SCENARIO 5  Missed stop: user stays on the bus past Domlur (destination Indiranagar)")
t = c.post("/api/trips", json={"bus_number": "335E", "boarding_stop": "Majestic",
                               "destination": "Indiranagar"}).get_json()["trip_id"]
say(c.post(f"/api/trips/{t}/location", json={"lat": 12.9609, "lng": 77.6387, "lang": L}))

step("SCENARIO 6  Emergency: user presses the SOS button")
c.post("/api/contacts", json={"name": "Amma", "phone": "+919876543210", "relation": "Mother"})
d = say(c.post("/api/sos", json={"lat": 12.9770, "lng": 77.5715, "lang": L}))
print(f"  SMS TEXT: {d['message_to_send']}")
print(f"  NOTIFY  : {[x['name'] + ' ' + x['phone'] for x in d['contacts']]}")
print("\nDemo complete.")
