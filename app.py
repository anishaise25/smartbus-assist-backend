"""Flask API for bus route detection."""
from flask import Flask, jsonify, request

import db
import gps
import routes_logic as rl
import speech
import voice
from i18n import norm_lang, tr
from seed_data import seed


def create_app(db_path=None):
    app = Flask(__name__)
    path = db_path or db.DEFAULT_DB
    seed(path).close()

    def conn():
        return db.connect(path)

    class ApiError(Exception):
        def __init__(self, msg, code=400):
            self.msg, self.code = msg, code

    @app.errorhandler(ApiError)
    def _api_err(e):
        return jsonify({"error": e.msg}), e.code

    @app.errorhandler(404)
    def _404(_):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def _500(_):
        return jsonify({"error": "server error"}), 500

    @app.after_request
    def _cors(resp):  # lets the frontend (another origin) call the API
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
        return resp

    # ---------- helpers ----------
    def need_stop(c, q, label):
        row = rl.resolve_stop(c, q)
        if not row:
            raise ApiError(f"{label} stop not found: {q!r}", 404)
        return row

    def num(name, source):
        try:
            return float(source.get(name))
        except (TypeError, ValueError):
            raise ApiError(f"'{name}' must be a number")

    def get_lang(body=None):
        """Language for spoken text: ?lang=kn|hi|en (query string or JSON body)."""
        return norm_lang(request.args.get("lang") or (body or {}).get("lang"))

    def stop_json(r):
        return {"id": r["id"], "name": r["name"], "lat": r["lat"], "lng": r["lng"]}

    # ---------- health ----------
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # ---------- stops ----------
    @app.get("/api/stops")
    def list_stops():
        q = request.args.get("q", "").strip()
        c = conn()
        rows = c.execute("SELECT * FROM stops WHERE name LIKE ? ORDER BY name", (f"%{q}%",)).fetchall()
        return jsonify([stop_json(r) for r in rows])

    @app.post("/api/stops")
    def add_stop():
        d = request.get_json(silent=True) or {}
        if not d.get("name"):
            raise ApiError("'name' is required")
        lat, lng = num("lat", d), num("lng", d)
        c = conn()
        try:
            cur = c.execute("INSERT INTO stops(name, lat, lng) VALUES (?,?,?)", (d["name"], lat, lng))
            c.commit()
        except Exception:
            raise ApiError("stop name already exists", 409)
        return jsonify({"id": cur.lastrowid, "name": d["name"], "lat": lat, "lng": lng}), 201

    @app.get("/api/stops/<int:stop_id>/buses")
    def buses_at_stop(stop_id):
        c = conn()
        s = need_stop(c, stop_id, "")
        rows = c.execute("""SELECT b.number, b.name, b.bus_type FROM buses b
                            JOIN route_stops rs ON rs.bus_id = b.id
                            WHERE rs.stop_id = ? ORDER BY b.number""", (stop_id,)).fetchall()
        return jsonify({"stop": stop_json(s), "buses": [dict(r) for r in rows]})

    # ---------- buses ----------
    def bus_detail(c, bus_row):
        stops = c.execute("""SELECT s.id, s.name, s.lat, s.lng, rs.seq FROM route_stops rs
                             JOIN stops s ON s.id = rs.stop_id
                             WHERE rs.bus_id = ? ORDER BY rs.seq""", (bus_row["id"],)).fetchall()
        return {"number": bus_row["number"], "name": bus_row["name"], "bus_type": bus_row["bus_type"],
                "bidirectional": bool(bus_row["bidirectional"]),
                "num_stops": len(stops), "stops": [dict(s) for s in stops]}

    @app.get("/api/buses")
    def list_buses():
        c = conn()
        rows = c.execute("""SELECT b.number, b.name, b.bus_type, COUNT(rs.seq) AS num_stops
                            FROM buses b LEFT JOIN route_stops rs ON rs.bus_id = b.id
                            GROUP BY b.id ORDER BY b.number""").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/api/buses/<number>")
    def get_bus(number):
        c = conn()
        b = c.execute("SELECT * FROM buses WHERE number = ?", (number,)).fetchone()
        if not b:
            raise ApiError("bus not found", 404)
        return jsonify(bus_detail(c, b))

    @app.post("/api/buses")
    def add_bus():
        """Body: {number, name, bus_type, bidirectional, stops: [id | "name" | {name,lat,lng}, ...]}"""
        d = request.get_json(silent=True) or {}
        if not d.get("number") or len(d.get("stops", [])) < 2:
            raise ApiError("'number' and at least 2 'stops' are required")
        c = conn()
        if c.execute("SELECT 1 FROM buses WHERE number = ?", (d["number"],)).fetchone():
            raise ApiError("bus number already exists", 409)
        stop_ids = []
        for item in d["stops"]:
            if isinstance(item, dict):
                row = c.execute("SELECT id FROM stops WHERE name = ?", (item.get("name"),)).fetchone()
                if row:
                    sid = row["id"]
                else:
                    cur = c.execute("INSERT INTO stops(name, lat, lng) VALUES (?,?,?)",
                                    (item["name"], num("lat", item), num("lng", item)))
                    sid = cur.lastrowid
            else:
                sid = need_stop(c, item, "route")["id"]
            if sid in stop_ids:
                raise ApiError("a stop appears twice in the route")
            stop_ids.append(sid)
        cur = c.execute("INSERT INTO buses(number, name, bus_type, bidirectional) VALUES (?,?,?,?)",
                        (d["number"], d.get("name"), d.get("bus_type", "Ordinary"),
                         1 if d.get("bidirectional", True) else 0))
        for seq, sid in enumerate(stop_ids, 1):
            c.execute("INSERT INTO route_stops(bus_id, stop_id, seq) VALUES (?,?,?)",
                      (cur.lastrowid, sid, seq))
        c.commit()
        return jsonify(bus_detail(c, c.execute("SELECT * FROM buses WHERE id=?", (cur.lastrowid,)).fetchone())), 201

    @app.delete("/api/buses/<number>")
    def delete_bus(number):
        c = conn()
        cur = c.execute("DELETE FROM buses WHERE number = ?", (number,))
        c.commit()
        if not cur.rowcount:
            raise ApiError("bus not found", 404)
        return jsonify({"deleted": number})

    # ---------- route search ----------
    def resolve_endpoint(c, prefix):
        """Endpoint given as a stop (from/to) or as GPS coords (from_lat & from_lng)."""
        q = request.args.get(prefix)
        if q:
            return need_stop(c, q, prefix)
        if request.args.get(f"{prefix}_lat") and request.args.get(f"{prefix}_lng"):
            near = gps.nearest_stops(c, num(f"{prefix}_lat", request.args),
                                     num(f"{prefix}_lng", request.args), radius_m=2000, limit=1)
            if not near:
                raise ApiError(f"no bus stop within 2 km of the '{prefix}' location", 404)
            return need_stop(c, near[0]["id"], prefix)
        raise ApiError(f"provide '{prefix}' (stop name/id) or '{prefix}_lat' & '{prefix}_lng'")

    @app.get("/api/search")
    def search_route():
        """Source -> destination: direct buses + alternatives with transfers."""
        c = conn()
        src, dst = resolve_endpoint(c, "from"), resolve_endpoint(c, "to")
        if src["id"] == dst["id"]:
            raise ApiError("source and destination are the same stop")
        mt = min(max(int(request.args.get("max_transfers", 2)), 0), 3)
        res = rl.search(c, src, dst, max_transfers=mt, limit=int(request.args.get("limit", 5)))
        lang = get_lang()
        res["lang"] = lang
        res["speech"] = voice.search_summary(rl.get_network(c), res, lang)
        return jsonify(res)

    @app.get("/api/transfers")
    def transfers():
        """Only routes that need a bus change."""
        c = conn()
        src, dst = resolve_endpoint(c, "from"), resolve_endpoint(c, "to")
        res = rl.search(c, src, dst, max_transfers=min(int(request.args.get("max_transfers", 2)), 3))
        return jsonify({"from": res["from"], "to": res["to"], "transfer_routes": res["transfer_routes"],
                        "has_direct_bus": bool(res["direct_buses"])})

    # ---------- GPS ----------
    @app.get("/api/gps/nearest")
    def nearest():
        c = conn()
        res = gps.nearest_stops(c, num("lat", request.args), num("lng", request.args),
                                radius_m=int(request.args.get("radius", 1000)),
                                limit=int(request.args.get("limit", 5)))
        return jsonify(res)

    @app.post("/api/gps/detect")
    def detect():
        """Is the user at a bus stop right now? Also lists buses serving nearby stops."""
        d = request.get_json(silent=True) or {}
        c = conn()
        near = gps.nearest_stops(c, num("lat", d), num("lng", d), radius_m=500, limit=3)
        for s in near:
            s["buses"] = [r["number"] for r in c.execute(
                """SELECT b.number FROM buses b JOIN route_stops rs ON rs.bus_id=b.id
                   WHERE rs.stop_id=? ORDER BY b.number""", (s["id"],))]
        at_stop = near[0] if near and near[0]["distance_m"] <= gps.STOP_RADIUS_M else None
        return jsonify({"at_stop": at_stop, "nearby_stops": near})

    @app.post("/api/trips")
    def start_trip():
        """Body: {bus_number, destination, boarding_stop | lat+lng}. Starts GPS alert tracking."""
        d = request.get_json(silent=True) or {}
        c = conn()
        bus = c.execute("SELECT * FROM buses WHERE number = ?", (d.get("bus_number"),)).fetchone()
        if not bus:
            raise ApiError("bus not found", 404)
        dest = need_stop(c, d.get("destination"), "destination")
        if d.get("boarding_stop"):
            board = need_stop(c, d["boarding_stop"], "boarding")
        elif "lat" in d and "lng" in d:
            near = gps.nearest_stops(c, num("lat", d), num("lng", d), radius_m=1000, limit=1)
            if not near:
                raise ApiError("no bus stop near your location", 404)
            board = need_stop(c, near[0]["id"], "boarding")
        else:
            raise ApiError("provide 'boarding_stop' or 'lat' & 'lng'")
        route = [r["stop_id"] for r in c.execute(
            "SELECT stop_id FROM route_stops WHERE bus_id=? ORDER BY seq", (bus["id"],))]
        if board["id"] not in route or dest["id"] not in route:
            raise ApiError("boarding and destination must both be on this bus's route")
        if board["id"] == dest["id"]:
            raise ApiError("boarding and destination are the same stop")
        direction = 1 if route.index(dest["id"]) > route.index(board["id"]) else -1
        if direction == -1 and not bus["bidirectional"]:
            raise ApiError("this bus does not run in that direction")
        cur = c.execute("""INSERT INTO trips(bus_id, board_stop_id, dest_stop_id, direction, last_stop_id)
                           VALUES (?,?,?,?,?)""", (bus["id"], board["id"], dest["id"], direction, board["id"]))
        c.commit()
        return jsonify({"trip_id": cur.lastrowid, "bus_number": bus["number"],
                        "boarding": board["name"], "destination": dest["name"],
                        "direction": "forward" if direction == 1 else "reverse"}), 201

    @app.post("/api/trips/<int:trip_id>/location")
    def trip_location(trip_id):
        """Send the phone's GPS fix; returns current stop and an alert for the destination."""
        d = request.get_json(silent=True) or {}
        lat, lng = num("lat", d), num("lng", d)
        c = conn()
        trip = c.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
        if not trip:
            raise ApiError("trip not found", 404)
        if trip["status"] != "active":
            raise ApiError("trip already completed", 409)
        res = gps.evaluate_trip(rl.get_network(c), dict(trip), lat, lng, get_lang(d))
        status = "completed" if res["alert_level"] in ("arrived", "missed") else "active"
        c.execute("UPDATE trips SET last_stop_id=?, status=? WHERE id=?",
                  (res["current_stop"]["id"], status, trip_id))
        c.commit()
        res["trip_id"], res["trip_status"] = trip_id, status
        return jsonify(res)

    # ---------- AI bus-number identification (input: text from the camera/OCR model) ----------
    @app.post("/api/assist/identify-bus")
    def identify_bus():
        """Body: {detected_text, destination?, lat?, lng?, lang?}
        The vision/OCR model reads the bus board; this says whether to board."""
        d = request.get_json(silent=True) or {}
        lang = get_lang(d)
        c = conn()
        net = rl.get_network(c)
        bus, conf = speech.match_bus(net, d.get("detected_text"))
        if not bus:
            return jsonify({"identified": False, "lang": lang, "speech": tr(lang, "unreadable"),
                            "vibration": [150, 100, 150]})
        out = {"identified": True, "confidence": conf, "bus_number": bus["number"],
               "route_name": bus["name"], "lang": lang,
               "route_ends": [net.stops[bus["route"][0]]["name"], net.stops[bus["route"][-1]]["name"]]}
        dest_id, status, alt = None, None, None
        if d.get("destination"):
            dest = need_stop(c, d["destination"], "destination")
            dest_id = dest["id"]
            here = None
            if d.get("lat") is not None and d.get("lng") is not None:
                near = gps.nearest_stops(c, num("lat", d), num("lng", d), radius_m=1000, limit=1)
                here = near[0]["id"] if near else None
            if dest_id not in bus["route"]:
                status = "not_going"
                if here:
                    res = rl.search(c, c.execute("SELECT * FROM stops WHERE id=?", (here,)).fetchone(), dest)
                    if res["found"]:
                        alt = res["best"]
                        out["alternative"] = alt
            elif here and here in bus["route"] and net._segment(bus, here, dest_id) is None:
                status = "opposite"
            else:
                status = "board"
            out["should_board"] = status == "board"
        out["speech"] = voice.identify(net, bus, conf, lang, dest_id, status, alt)
        out["vibration"] = [300, 150, 300] if out.get("should_board") else [150]
        return jsonify(out)

    # ---------- Emergency contacts & SOS ----------
    @app.get("/api/contacts")
    def list_contacts():
        return jsonify([dict(r) for r in conn().execute("SELECT * FROM emergency_contacts")])

    @app.post("/api/contacts")
    def add_contact():
        d = request.get_json(silent=True) or {}
        if not d.get("name") or not d.get("phone"):
            raise ApiError("'name' and 'phone' are required")
        c = conn()
        cur = c.execute("INSERT INTO emergency_contacts(name, phone, relation) VALUES (?,?,?)",
                        (d["name"], d["phone"], d.get("relation")))
        c.commit()
        return jsonify({"id": cur.lastrowid, **{k: d.get(k) for k in ("name", "phone", "relation")}}), 201

    @app.delete("/api/contacts/<int:cid>")
    def delete_contact(cid):
        c = conn()
        cur = c.execute("DELETE FROM emergency_contacts WHERE id=?", (cid,))
        c.commit()
        if not cur.rowcount:
            raise ApiError("contact not found", 404)
        return jsonify({"deleted": cid})

    @app.post("/api/sos")
    def sos():
        """Body: {lat, lng, trip_id?, lang?}. Logs the event and returns a ready-to-send alert
        message plus the contacts to notify (the phone app sends the SMS / makes the call)."""
        d = request.get_json(silent=True) or {}
        lat, lng = num("lat", d), num("lng", d)
        lang = get_lang(d)
        c = conn()
        near = gps.nearest_stops(c, lat, lng, radius_m=1000, limit=1)
        link = f"https://maps.google.com/?q={lat},{lng}"
        c.execute("INSERT INTO sos_events(lat, lng, trip_id) VALUES (?,?,?)", (lat, lng, d.get("trip_id")))
        c.commit()
        contacts = [dict(r) for r in c.execute("SELECT * FROM emergency_contacts")]
        text, say = voice.sos(rl.get_network(c), near[0] if near else None, link, len(contacts), lang)
        return jsonify({"message_to_send": text, "contacts": contacts,
                        "nearest_stop": near[0] if near else None, "lang": lang,
                        "speech": say, "vibration": [800, 200, 800, 200, 800]})

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=True)
