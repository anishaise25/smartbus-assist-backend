"""Route search: stop lookup, direct buses, transfers, alternatives.
Fast enough for the full BMTC network (thousands of routes)."""
from collections import defaultdict
from gps import haversine_m

AVG_SPEED_KMPH = 18.0      # city bus average
DWELL_MIN = 0.5            # per stop
TRANSFER_WAIT_MIN = 7.0    # average wait when changing buses
TRANSFER_PENALTY_MIN = 15.0  # extra ranking cost per bus change: changes are hard for blind users
MAX_PAIRS_RESULTS = 300    # cap on 1-transfer candidates kept before ranking
BFS_FRONTIER_CAP = 40000   # safety cap for the 2-transfer search


class Network:
    """In-memory snapshot of stops, buses and routes."""

    def __init__(self, conn):
        self.stops = {r["id"]: dict(r) for r in conn.execute("SELECT * FROM stops")}
        self.translated = defaultdict(dict)
        for r in conn.execute("SELECT stop_id, lang, name FROM stop_names"):
            self.translated[r["stop_id"]][r["lang"]] = r["name"]
        self.buses = {}
        for b in conn.execute("SELECT * FROM buses"):
            self.buses[b["id"]] = {"id": b["id"], "number": b["number"], "name": b["name"],
                                   "bus_type": b["bus_type"],
                                   "bidirectional": bool(b["bidirectional"]), "route": []}
        for r in conn.execute("SELECT bus_id, stop_id FROM route_stops ORDER BY bus_id, seq"):
            self.buses[r["bus_id"]]["route"].append(r["stop_id"])
        self.pos, self.stop_buses = {}, defaultdict(list)
        for b in self.buses.values():
            self.pos[b["id"]] = {s: i for i, s in enumerate(b["route"])}
            for sid in b["route"]:
                self.stop_buses[sid].append(b["id"])

    def name(self, stop_id, lang="en"):
        if lang and lang != "en":
            return self.translated.get(stop_id, {}).get(lang) or self.stops[stop_id]["name"]
        return self.stops[stop_id]["name"]

    # ---- geometry -------------------------------------------------------
    def _dist_km(self, a, b):
        sa, sb = self.stops[a], self.stops[b]
        return haversine_m(sa["lat"], sa["lng"], sb["lat"], sb["lng"]) / 1000.0

    def _can_ride(self, bus, a, b):
        pos = self.pos[bus["id"]]
        return b != a and a in pos and b in pos and (pos[b] > pos[a] or bus["bidirectional"])

    def _segment(self, bus, a, b):
        if not self._can_ride(bus, a, b):
            return None
        route, pos = bus["route"], self.pos[bus["id"]]
        i, j = pos[a], pos[b]
        return route[i:j + 1] if j > i else route[j:i + 1][::-1]

    def _leg(self, bus, a, b):
        seg = self._segment(bus, a, b)
        if not seg:
            return None
        km = sum(self._dist_km(x, y) for x, y in zip(seg, seg[1:]))
        mins = km / AVG_SPEED_KMPH * 60 + DWELL_MIN * (len(seg) - 1)
        return {
            "bus_number": bus["number"], "bus_name": bus["name"], "bus_type": bus["bus_type"],
            "board_at": self.stops[a]["name"], "get_off_at": self.stops[b]["name"],
            "board_stop_id": a, "get_off_stop_id": b,
            "num_stops": len(seg) - 1,
            "distance_km": round(km, 1), "minutes": round(mins),
            "stops": [{"id": s, "name": self.stops[s]["name"]} for s in seg],
            "_bus_id": bus["id"], "_from": a, "_to": b,
        }

    def _reachable(self, bus, cur):
        route, i = bus["route"], self.pos[bus["id"]][cur]
        for j in range(i + 1, len(route)):
            yield route[j]
        if bus["bidirectional"]:
            for j in range(i - 1, -1, -1):
                yield route[j]

    # ---- search ---------------------------------------------------------
    def _direct_and_one_transfer(self, src, dst):
        out = []
        src_buses, dst_buses = self.stop_buses.get(src, []), self.stop_buses.get(dst, [])
        for a in src_buses:                                   # direct
            leg = self._leg(self.buses[a], src, dst)
            if leg:
                out.append([leg])
        cands = []                                            # one transfer
        dst_set = set(dst_buses)
        for a in src_buses:
            A = self.buses[a]
            ra = set(A["route"])
            for b in dst_set:
                if b == a:
                    continue
                B = self.buses[b]
                best_t, best_n = None, None
                for t in ra.intersection(B["route"]):
                    if t in (src, dst) or not (self._can_ride(A, src, t) and self._can_ride(B, t, dst)):
                        continue
                    n = abs(self.pos[a][t] - self.pos[a][src]) + abs(self.pos[b][dst] - self.pos[b][t])
                    if best_n is None or n < best_n:
                        best_t, best_n = t, n
                if best_t is not None:
                    cands.append((best_n, a, b, best_t))
        cands.sort()
        for _, a, b, t in cands[:MAX_PAIRS_RESULTS]:
            out.append([self._leg(self.buses[a], src, t), self._leg(self.buses[b], t, dst)])
        return out

    def _bfs(self, src, dst, max_transfers):
        results = []
        frontier = [(src, [], frozenset(), (src,))]
        for depth in range(max_transfers + 1):
            nxt = []
            for cur, legs, used, visited in frontier:
                for bid in self.stop_buses.get(cur, []):
                    if bid in used:
                        continue
                    bus = self.buses[bid]
                    for to in self._reachable(bus, cur):
                        if to in visited:
                            continue
                        if to == dst:
                            results.append(legs + [self._leg(bus, cur, to)])
                        elif depth < max_transfers and len(self.stop_buses[to]) > 1 \
                                and len(nxt) < BFS_FRONTIER_CAP:
                            nxt.append((to, legs + [self._leg(bus, cur, to)], used | {bid}, visited + (to,)))
            frontier = nxt
        return results

    def find_journeys(self, src, dst, max_transfers=2):
        results = self._direct_and_one_transfer(src, dst) if max_transfers >= 1 else \
            [l for l in self._direct_and_one_transfer(src, dst) if len(l) == 1]
        small = len(self.buses) <= 50
        if max_transfers >= 2 and (small or not results):
            results += [r for r in self._bfs(src, dst, 2) if len(r) == 3 or small]
        results = [legs for legs in results if not self._has_pointless_change(legs)]
        seen, unique = set(), []
        for legs in results:
            key = tuple((l["_bus_id"], l["_from"], l["_to"]) for l in legs)
            if key not in seen:
                seen.add(key)
                unique.append(legs)
        return [self._journey(legs) for legs in unique]

    def _has_pointless_change(self, legs):
        """True if a later bus could already be boarded at an earlier leg's boarding stop
        (so the earlier legs and the bus change add nothing)."""
        for i in range(len(legs)):
            for j in range(i + 1, len(legs)):
                if self._can_ride(self.buses[legs[j]["_bus_id"]], legs[i]["_from"], legs[j]["_to"]):
                    return True
        return False

    def _journey(self, legs):
        transfers = len(legs) - 1
        total = sum(l["minutes"] for l in legs) + TRANSFER_WAIT_MIN * transfers
        steps = []
        for i, l in enumerate(legs):
            verb = "Board" if i == 0 else "Change to"
            steps.append(f"{verb} bus {l['bus_number']} at {l['board_at']} and ride "
                         f"{l['num_stops']} stop{'s' if l['num_stops'] != 1 else ''} to {l['get_off_at']}.")
        clean = [{k: v for k, v in l.items() if not k.startswith("_")} for l in legs]
        return {
            "type": "direct" if transfers == 0 else f"{transfers}-transfer",
            "transfers": transfers,
            "transfer_points": [l["get_off_at"] for l in legs[:-1]],
            "buses": [l["bus_number"] for l in legs],
            "total_stops": sum(l["num_stops"] for l in legs),
            "total_minutes": round(total),
            "legs": clean,
            "instructions": steps,
            "_score": total + TRANSFER_PENALTY_MIN * transfers,
        }


# ---- cached network ------------------------------------------------------
_CACHE = {}


def get_network(conn):
    """Reuse the in-memory network until the data changes."""
    path = conn.execute("PRAGMA database_list").fetchone()[2]
    stamp = conn.execute("""SELECT (SELECT COUNT(*) FROM stops) || '-' || (SELECT COUNT(*) FROM buses) || '-' ||
                                   (SELECT COUNT(*) FROM route_stops) || '-' || (SELECT COUNT(*) FROM stop_names) || '-' ||
                                   IFNULL((SELECT MAX(id) FROM buses), 0)""").fetchone()[0]
    hit = _CACHE.get(path)
    if hit and hit[0] == stamp:
        return hit[1]
    net = Network(conn)
    _CACHE[path] = (stamp, net)
    return net


# ---- stop lookup ---------------------------------------------------------
def resolve_stop(conn, q):
    """Accept a stop id or a (partial, case-insensitive) name in English, Kannada or Hindi."""
    if q is None or str(q).strip() == "":
        return None
    q = str(q).strip()
    if q.isdigit():
        r = conn.execute("SELECT * FROM stops WHERE id = ?", (int(q),)).fetchone()
        if r:
            return r
    r = conn.execute("SELECT * FROM stops WHERE name = ?", (q,)).fetchone()
    if r:
        return r
    r = conn.execute("""SELECT s.* FROM stops s JOIN stop_names n ON n.stop_id = s.id
                        WHERE n.name = ? LIMIT 1""", (q,)).fetchone()
    if r:
        return r
    r = conn.execute("SELECT * FROM stops WHERE name LIKE ? ORDER BY length(name) LIMIT 1",
                     (f"%{q}%",)).fetchone()
    if r:
        return r
    return conn.execute("""SELECT s.* FROM stops s JOIN stop_names n ON n.stop_id = s.id
                           WHERE n.name LIKE ? ORDER BY length(n.name) LIMIT 1""", (f"%{q}%",)).fetchone()


def search(conn, src_row, dst_row, max_transfers=2, limit=5):
    net = get_network(conn)
    journeys = net.find_journeys(src_row["id"], dst_row["id"], max_transfers)
    journeys.sort(key=lambda j: j["_score"])
    for j in journeys:
        j.pop("_score")
    direct = [j for j in journeys if j["transfers"] == 0]
    transfer = [j for j in journeys if j["transfers"] > 0][:limit]
    return {
        "from": {"id": src_row["id"], "name": src_row["name"]},
        "to": {"id": dst_row["id"], "name": dst_row["name"]},
        "direct_buses": direct,
        "transfer_routes": transfer,
        "best": (direct or transfer or [None])[0],
        "found": bool(direct or transfer),
    }
