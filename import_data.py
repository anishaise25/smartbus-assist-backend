"""Load real bus data into the database.

  GTFS (e.g. the community BMTC feed):
      python import_data.py gtfs path/to/bmtc_gtfs_folder --replace [--max-routes 500]
  CSV (hand-made data):
      python import_data.py csv stops.csv routes.csv --replace

GTFS needs stops.txt, routes.txt, trips.txt, stop_times.txt (unzip the feed first).
Where to get BMTC data: the community feed github.com/Vonter/bmtc-gtfs (file gtfs/bmtc.zip,
~4,400 routes with full stop sequences) or the official BMTC feed on hub.tumidata.org / data.opencity.in.
Check each source's licence and freshness before using it.

stops.csv  : name,lat,lng[,name_kn,name_hi]
routes.csv : bus_number,bus_name,bus_type,seq,stop_name      (one row per stop of the route)
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

import db
from gps import haversine_m

MERGE_RADIUS_M = 300   # same-named stops closer than this are treated as one stop


def clear(conn):
    for t in ("trips", "route_stops", "buses", "stop_names", "stops"):
        conn.execute(f"DELETE FROM {t}")
    conn.commit()


def _add_stop(conn, cache, name, lat, lng):
    """Insert a stop, merging same-name stops that are very close; returns db id."""
    name = name.strip()
    for sid, (slat, slng) in cache.get(name.lower(), []):
        if haversine_m(lat, lng, slat, slng) <= MERGE_RADIUS_M:
            return sid
    unique = name
    if name.lower() in cache:                      # same name, far away -> disambiguate
        unique = f"{name} ({len(cache[name.lower()]) + 1})"
    cur = conn.execute("INSERT INTO stops(name, lat, lng) VALUES (?,?,?)", (unique, lat, lng))
    cache[name.lower()].append((cur.lastrowid, (lat, lng)))
    return cur.lastrowid


def _add_bus(conn, number, name, btype, stop_ids):
    seen, ordered = set(), []
    for s in stop_ids:                              # drop repeated stops (loop routes)
        if s not in seen:
            seen.add(s)
            ordered.append(s)
    if len(ordered) < 2:
        return False
    cur = conn.execute("INSERT INTO buses(number, name, bus_type) VALUES (?,?,?)",
                       (number, name, btype))
    conn.executemany("INSERT INTO route_stops(bus_id, stop_id, seq) VALUES (?,?,?)",
                     [(cur.lastrowid, s, i) for i, s in enumerate(ordered, 1)])
    return True


def import_gtfs(conn, folder, max_routes=None):
    def rows(name):
        with open(os.path.join(folder, name), newline="", encoding="utf-8-sig") as f:
            yield from csv.DictReader(f)

    stops = {r["stop_id"]: (r["stop_name"], float(r["stop_lat"]), float(r["stop_lon"]))
             for r in rows("stops.txt") if r.get("stop_lat") and r.get("stop_lon")}
    routes = {r["route_id"]: r for r in rows("routes.txt")}
    trip_route = {r["trip_id"]: r["route_id"] for r in rows("trips.txt")}

    count = defaultdict(int)                        # pass 1: stops per trip
    for r in rows("stop_times.txt"):
        count[r["trip_id"]] += 1
    best = {}                                       # longest trip per route
    for trip, route in trip_route.items():
        if route in routes and count.get(trip, 0) > count.get(best.get(route), 0):
            best[route] = trip
    chosen = {t: r for r, t in best.items()}

    seqs = defaultdict(list)                        # pass 2: ordered stops of chosen trips
    for r in rows("stop_times.txt"):
        if r["trip_id"] in chosen:
            seqs[r["trip_id"]].append((int(r["stop_sequence"]), r["stop_id"]))

    candidates = {}                                 # keep the longest route per bus number
    for trip, route_id in chosen.items():
        ids = [sid for _, sid in sorted(seqs[trip]) if sid in stops]
        rt = routes[route_id]
        number = (rt.get("route_short_name") or rt.get("route_long_name") or route_id).strip()
        if number not in candidates or len(ids) > len(candidates[number][2]):
            candidates[number] = (rt.get("route_long_name") or number, "Ordinary", ids)

    items = sorted(candidates.items(), key=lambda kv: -len(kv[1][2]))
    if max_routes:
        items = items[:max_routes]
    cache, id_map, added = defaultdict(list), {}, 0
    for number, (name, btype, ids) in items:
        mapped = []
        for sid in ids:
            if sid not in id_map:
                n, lat, lng = stops[sid]
                id_map[sid] = _add_stop(conn, cache, n, lat, lng)
            mapped.append(id_map[sid])
        added += _add_bus(conn, number, name, btype, mapped)
    conn.commit()
    return added, len(id_map)


def import_csv(conn, stops_csv, routes_csv):
    cache, ids = defaultdict(list), {}
    with open(stops_csv, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            sid = _add_stop(conn, cache, r["name"], float(r["lat"]), float(r["lng"]))
            ids[r["name"].strip().lower()] = sid
            for lang in ("kn", "hi"):
                if r.get(f"name_{lang}"):
                    conn.execute("INSERT OR REPLACE INTO stop_names VALUES (?,?,?)",
                                 (sid, lang, r[f"name_{lang}"].strip()))
    buses = defaultdict(lambda: {"name": None, "type": "Ordinary", "stops": []})
    with open(routes_csv, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            b = buses[r["bus_number"].strip()]
            b["name"], b["type"] = r.get("bus_name") or b["name"], r.get("bus_type") or b["type"]
            key = r["stop_name"].strip().lower()
            if key not in ids:
                raise SystemExit(f"routes.csv uses unknown stop {r['stop_name']!r} (add it to stops.csv)")
            b["stops"].append((int(r["seq"]), ids[key]))
    added = sum(_add_bus(conn, num, b["name"], b["type"], [s for _, s in sorted(b["stops"])])
                for num, b in buses.items())
    conn.commit()
    return added, len(ids)


def export_csv(conn, folder):
    """Dump the current data to stops.csv / routes.csv (handy as a template)."""
    os.makedirs(folder, exist_ok=True)
    names = defaultdict(dict)
    for r in conn.execute("SELECT * FROM stop_names"):
        names[r["stop_id"]][r["lang"]] = r["name"]
    with open(os.path.join(folder, "stops.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "lat", "lng", "name_kn", "name_hi"])
        for r in conn.execute("SELECT * FROM stops ORDER BY id"):
            w.writerow([r["name"], r["lat"], r["lng"], names[r["id"]].get("kn", ""), names[r["id"]].get("hi", "")])
    with open(os.path.join(folder, "routes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bus_number", "bus_name", "bus_type", "seq", "stop_name"])
        for r in conn.execute("""SELECT b.number, b.name, b.bus_type, rs.seq, s.name AS sname
                                 FROM route_stops rs JOIN buses b ON b.id = rs.bus_id
                                 JOIN stops s ON s.id = rs.stop_id ORDER BY b.number, rs.seq"""):
            w.writerow([r["number"], r["name"], r["bus_type"], r["seq"], r["sname"]])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["gtfs", "csv", "export"])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--db", default=db.DEFAULT_DB)
    ap.add_argument("--replace", action="store_true", help="wipe existing stops/buses first")
    ap.add_argument("--max-routes", type=int, help="gtfs: import only the N longest routes")
    a = ap.parse_args()
    conn = db.init_db(a.db)
    if a.replace:
        clear(conn)
    if a.mode == "gtfs":
        n, s = import_gtfs(conn, a.paths[0], a.max_routes)
    elif a.mode == "csv":
        if len(a.paths) != 2:
            sys.exit("csv mode needs: stops.csv routes.csv")
        n, s = import_csv(conn, *a.paths)
    else:
        export_csv(conn, a.paths[0]); sys.exit(print("Exported to", a.paths[0]))
    print(f"Imported {n} bus routes and {s} stops into {a.db}")
