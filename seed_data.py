"""Sample Bengaluru data. Bus numbers/routes are ILLUSTRATIVE - replace with real BMTC data."""
from db import init_db
from i18n import STOP_NAMES

STOPS = {
    "Majestic": (12.9767, 77.5713), "KR Market": (12.9648, 77.5775),
    "Shivajinagar": (12.9857, 77.6057), "MG Road": (12.9756, 77.6066),
    "Indiranagar": (12.9784, 77.6408), "Domlur": (12.9609, 77.6387),
    "Marathahalli": (12.9569, 77.7011), "Whitefield": (12.9698, 77.7500),
    "Koramangala": (12.9352, 77.6245), "Silk Board": (12.9177, 77.6233),
    "BTM Layout": (12.9166, 77.6101), "Jayanagar 4th Block": (12.9250, 77.5938),
    "Banashankari": (12.9255, 77.5468), "HSR Layout": (12.9116, 77.6474),
    "Bellandur": (12.9304, 77.6784), "Electronic City": (12.8452, 77.6602),
    "Hebbal": (13.0358, 77.5970), "Mekhri Circle": (13.0136, 77.5832),
    "Malleshwaram": (13.0035, 77.5643), "Yeshwanthpur": (13.0285, 77.5409),
    "Vijayanagar": (12.9719, 77.5300), "Kengeri": (12.9177, 77.4833),
    "Kempegowda Airport": (13.1986, 77.7066),
}

BUSES = [  # number, name, type, stop list in order
    ("335E", "Majestic - Whitefield", "Ordinary",
     ["Majestic", "Shivajinagar", "MG Road", "Indiranagar", "Domlur", "Marathahalli", "Whitefield"]),
    ("500D", "Hebbal - Electronic City", "AC",
     ["Hebbal", "Mekhri Circle", "Shivajinagar", "MG Road", "Domlur", "Koramangala",
      "Silk Board", "Electronic City"]),
    ("G4", "Majestic - Bellandur", "Ordinary",
     ["Majestic", "KR Market", "Jayanagar 4th Block", "BTM Layout", "Silk Board",
      "HSR Layout", "Bellandur"]),
    ("201", "Majestic - Banashankari", "Ordinary",
     ["Majestic", "KR Market", "Jayanagar 4th Block", "Banashankari"]),
    ("KIA-9", "Majestic - Airport", "AC",
     ["Majestic", "Mekhri Circle", "Hebbal", "Kempegowda Airport"]),
    ("252", "Kengeri - Shivajinagar", "Ordinary",
     ["Kengeri", "Vijayanagar", "Majestic", "Shivajinagar"]),
    ("Y10", "Yeshwanthpur - KR Market", "Ordinary",
     ["Yeshwanthpur", "Malleshwaram", "Majestic", "KR Market"]),
    ("MH1", "Marathahalli - Banashankari", "Ordinary",
     ["Marathahalli", "Bellandur", "HSR Layout", "Silk Board", "BTM Layout",
      "Jayanagar 4th Block", "Banashankari"]),
]


def seed(path=None):
    conn = init_db(path)
    if conn.execute("SELECT COUNT(*) FROM stops").fetchone()[0]:
        return conn  # already seeded
    for name, (lat, lng) in STOPS.items():
        conn.execute("INSERT INTO stops(name, lat, lng) VALUES (?,?,?)", (name, lat, lng))
    ids = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM stops")}
    for number, name, btype, stops in BUSES:
        cur = conn.execute("INSERT INTO buses(number, name, bus_type) VALUES (?,?,?)",
                           (number, name, btype))
        for seq, s in enumerate(stops, 1):
            conn.execute("INSERT INTO route_stops(bus_id, stop_id, seq) VALUES (?,?,?)",
                         (cur.lastrowid, ids[s], seq))
    for en, (kn, hi) in STOP_NAMES.items():
        conn.execute("INSERT INTO stop_names VALUES (?,?,?)", (ids[en], "kn", kn))
        conn.execute("INSERT INTO stop_names VALUES (?,?,?)", (ids[en], "hi", hi))
    conn.commit()
    return conn


if __name__ == "__main__":
    seed()
    print("Database seeded.")
