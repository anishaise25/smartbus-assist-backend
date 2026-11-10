import os, tempfile
from app import create_app

app = create_app(os.path.join(tempfile.mkdtemp(), "t.db"))
c = app.test_client()

def ok(r, code=200):
    assert r.status_code == code, (r.status_code, r.get_json())
    return r.get_json()

def test_basic_lists():
    assert len(ok(c.get("/api/stops"))) >= 20
    assert len(ok(c.get("/api/buses"))) >= 8
    assert ok(c.get("/api/buses/335E"))["num_stops"] == 7

def test_direct_and_reverse():
    r = ok(c.get("/api/search?from=Majestic&to=Whitefield"))
    assert r["direct_buses"][0]["buses"] == ["335E"]
    r = ok(c.get("/api/search?from=Whitefield&to=Majestic"))   # reverse direction
    assert r["direct_buses"]

def test_transfer():
    r = ok(c.get("/api/search?from=Banashankari&to=Whitefield"))
    assert not r["direct_buses"] and r["transfer_routes"]
    print(r["best"]["instructions"])
    r = ok(c.get("/api/search?from=Kengeri&to=Electronic City"))
    assert r["found"]

def test_gps_search_and_detect():
    r = ok(c.get("/api/search?from_lat=12.9768&from_lng=77.5715&to=Hebbal"))
    assert r["from"]["name"] == "Majestic"
    d = ok(c.post("/api/gps/detect", json={"lat": 12.9767, "lng": 77.5713}))
    assert d["at_stop"]["name"] == "Majestic"

def test_trip_alerts():
    t = ok(c.post("/api/trips", json={"bus_number": "335E", "boarding_stop": "Majestic",
                                      "destination": "Marathahalli"}), 201)["trip_id"]
    lv = lambda lat, lng: ok(c.post(f"/api/trips/{t}/location", json={"lat": lat, "lng": lng}))
    assert lv(12.9767, 77.5713)["alert_level"] == "on_route"
    assert lv(12.9784, 77.6408)["alert_level"] == "approaching"   # Indiranagar, 2 stops away
    assert lv(12.9609, 77.6387)["alert_level"] == "next_stop"     # Domlur
    a = lv(12.9569, 77.7011)
    assert a["alert_level"] == "arrived" and a["trip_status"] == "completed"

def test_add_bus_and_errors():
    ok(c.post("/api/buses", json={"number": "X1", "stops": ["Majestic", "Hebbal"]}), 201)
    assert ok(c.get("/api/search?from=Majestic&to=Hebbal"))["direct_buses"]
    ok(c.get("/api/search?from=Nowhere&to=Hebbal"), 404)
    ok(c.get("/api/search?from=Majestic"), 400)

def test_speech_in_search():
    r = ok(c.get("/api/search?from=Majestic&to=Whitefield"))
    assert "Bus 335E goes directly" in r["speech"]
    assert r["direct_buses"][0]["speech"]

def test_identify_bus():
    r = ok(c.post("/api/assist/identify-bus", json={"detected_text": "335 E", "destination": "Whitefield"}))
    assert r["bus_number"] == "335E" and r["should_board"]
    r = ok(c.post("/api/assist/identify-bus", json={"detected_text": "5OOD"}))   # OCR read O as 0
    assert r["bus_number"] == "500D"
    r = ok(c.post("/api/assist/identify-bus", json={"detected_text": "xyz", "lat": 12.9767, "lng": 77.5713}))
    assert not r["identified"]
    # wrong bus for destination: from Majestic, 201 does not reach Whitefield -> alternative offered
    r = ok(c.post("/api/assist/identify-bus", json={"detected_text": "201", "destination": "Whitefield",
                                                    "lat": 12.9767, "lng": 77.5713}))
    assert not r["should_board"] and "335E" in r["speech"]
    # right bus, wrong direction
    r = ok(c.post("/api/assist/identify-bus", json={"detected_text": "KIA-9", "destination": "Majestic",
                                                    "lat": 13.1986, "lng": 77.7066}))
    assert r["should_board"]  # bidirectional

def test_alert_has_speech_and_vibration():
    t = ok(c.post("/api/trips", json={"bus_number": "201", "boarding_stop": "Majestic",
                                      "destination": "Banashankari"}), 201)["trip_id"]
    a = ok(c.post(f"/api/trips/{t}/location", json={"lat": 12.9255, "lng": 77.5468}))
    assert a["speech"] and a["vibration"] == [500, 200, 500, 200, 500]

def test_sos():
    ok(c.post("/api/contacts", json={"name": "Mom", "phone": "+911234567890"}), 201)
    r = ok(c.post("/api/sos", json={"lat": 12.9767, "lng": 77.5713}))
    assert "Majestic" in r["message_to_send"] and len(r["contacts"]) == 1

def test_languages():
    kn = ok(c.get("/api/search?from=Majestic&to=Whitefield&lang=kn"))
    assert "ವೈಟ್‌ಫೀಲ್ಡ್" in kn["speech"] and "335E" in kn["speech"]
    hi = ok(c.get("/api/search?from=Majestic&to=Whitefield&lang=hi"))
    assert "सीधी जाती है" in hi["speech"]
    assert ok(c.get("/api/search?from=Majestic&to=Whitefield&lang=xx"))["lang"] == "en"
    # stop names can be typed/spoken in Kannada or Hindi
    assert ok(c.get("/api/search?from=ಮೆಜೆಸ್ಟಿಕ್&to=व्हाइटफ़ील्ड"))["found"]
    r = ok(c.post("/api/assist/identify-bus", json={"detected_text": "201", "lang": "kn"}))
    assert "ಬಸ್ ಸಂಖ್ಯೆ 201" in r["speech"]
    t = ok(c.post("/api/trips", json={"bus_number": "201", "boarding_stop": "Majestic",
                                      "destination": "Banashankari"}), 201)["trip_id"]
    a = ok(c.post(f"/api/trips/{t}/location", json={"lat": 12.9255, "lng": 77.5468, "lang": "hi"}))
    assert "बनशंकरी" in a["speech"]
    s = ok(c.post("/api/sos", json={"lat": 12.9767, "lng": 77.5713, "lang": "kn"}))
    assert "ಮೆಜೆಸ್ಟಿಕ್" in s["message_to_send"]

def test_csv_import_roundtrip():
    import import_data, db
    from seed_data import seed
    d = tempfile.mkdtemp()
    import_data.export_csv(seed(os.path.join(d, "a.db")), d)
    fresh = db.init_db(os.path.join(d, "fresh.db"))
    n, s_ = import_data.import_csv(fresh, os.path.join(d, "stops.csv"), os.path.join(d, "routes.csv"))
    assert n == 8 and s_ == 23
    assert fresh.execute("SELECT COUNT(*) FROM stop_names").fetchone()[0] == 46

def test_gtfs_import():
    import import_data, db, csv
    d = tempfile.mkdtemp()
    def w(name, header, rows):
        with open(os.path.join(d, name), "w", newline="") as f:
            cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
    w("stops.txt", ["stop_id","stop_name","stop_lat","stop_lon"],
      [[1,"Alpha",12.90,77.50],[2,"Beta",12.92,77.52],[3,"Gamma",12.94,77.54],[4,"Beta",12.9201,77.5201]])
    w("routes.txt", ["route_id","route_short_name","route_long_name"], [["r1","A1","Alpha-Gamma"],["r2","A1","dup"]])
    w("trips.txt", ["route_id","trip_id"], [["r1","t1"],["r2","t2"]])
    w("stop_times.txt", ["trip_id","stop_id","stop_sequence"],
      [["t1",1,1],["t1",2,2],["t1",3,3],["t2",1,1],["t2",4,2]])
    conn = db.init_db(os.path.join(d, "g.db"))
    n, s = import_data.import_gtfs(conn, d)
    assert n == 1 and s == 3          # duplicate bus number collapsed, same-name nearby stops merged

def test_large_network_speed():
    import random, time, db
    random.seed(1)
    p = os.path.join(tempfile.mkdtemp(), "big.db")
    conn = db.init_db(p)
    for i in range(3000):
        conn.execute("INSERT INTO stops(name, lat, lng) VALUES (?,?,?)",
                     (f"S{i}", 12.8 + random.random() * .3, 77.4 + random.random() * .3))
    for b in range(3000):
        cur = conn.execute("INSERT INTO buses(number, name) VALUES (?,?)", (f"B{b}", f"route {b}"))
        for seq, sid in enumerate(random.sample(range(1, 3001), 45), 1):
            conn.execute("INSERT INTO route_stops VALUES (?,?,?)", (cur.lastrowid, sid, seq))
    conn.commit(); conn.close()
    big = create_app(p).test_client()
    big.get("/api/search?from=S1&to=S2")                     # warm the cache
    t0 = time.time()
    for q in ("S10&to=S2000", "S500&to=S1500", "S7&to=S2999"):
        r = ok(big.get(f"/api/search?from={q}"))
        assert r["found"]
    per = (time.time() - t0) / 3
    print(f"   large network: {per:.2f}s per search")
    assert per < 3

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("PASS", n)
