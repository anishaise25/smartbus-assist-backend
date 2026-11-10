"""GPS helpers: distance, nearest-stop detection, trip alert logic."""
import math

from speech import VIBRATION
from i18n import tr

STOP_RADIUS_M = 100       # "you are at this stop"
OFF_ROUTE_M = 500         # farther than this from every stop on the bus route = off route


def haversine_m(lat1, lng1, lat2, lng2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_stops(conn, lat, lng, radius_m=1000, limit=5):
    """Return stops within radius_m of the point, closest first."""
    # cheap bounding-box prefilter, then exact haversine
    dlat = radius_m / 111000.0
    dlng = radius_m / (111000.0 * max(math.cos(math.radians(lat)), 0.01))
    rows = conn.execute(
        "SELECT * FROM stops WHERE lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?",
        (lat - dlat, lat + dlat, lng - dlng, lng + dlng),
    ).fetchall()
    out = []
    for r in rows:
        d = haversine_m(lat, lng, r["lat"], r["lng"])
        if d <= radius_m:
            out.append({"id": r["id"], "name": r["name"], "lat": r["lat"], "lng": r["lng"],
                        "distance_m": round(d)})
    out.sort(key=lambda s: s["distance_m"])
    return out[:limit]


def evaluate_trip(net, trip, lat, lng, lang="en"):
    """Work out where the passenger is on the bus route and what alert to raise."""
    bus = net.buses[trip["bus_id"]]
    route = bus["route"]
    direction = trip["direction"]
    dest = net.stops[trip["dest_stop_id"]]
    dest_name = net.name(dest["id"], lang)

    # nearest stop on this bus's route to the GPS fix
    cur_id = min(route, key=lambda s: haversine_m(lat, lng, net.stops[s]["lat"], net.stops[s]["lng"]))
    cur = net.stops[cur_id]
    dist_cur = haversine_m(lat, lng, cur["lat"], cur["lng"])
    dist_dest = haversine_m(lat, lng, dest["lat"], dest["lng"])

    remaining = (route.index(dest["id"]) - route.index(cur_id)) * direction
    nxt_i = route.index(cur_id) + direction
    next_stop = net.stops[route[nxt_i]]["name"] if 0 <= nxt_i < len(route) else None

    if dist_dest <= STOP_RADIUS_M or (remaining == 0 and dist_dest <= 3 * STOP_RADIUS_M):
        level, msg = "arrived", tr(lang, "arrived", dest=dest_name)
    elif remaining < 0:
        level, msg = "missed", tr(lang, "missed", dest=dest_name)
    elif remaining == 1:
        level, msg = "next_stop", tr(lang, "next_stop", dest=dest_name)
    elif remaining <= 2 or dist_dest <= 800:
        level, msg = "approaching", tr(lang, "approaching", dest=dest_name, n=max(remaining, 1))
    else:
        level, msg = "on_route", tr(lang, "on_route", dest=dest_name, n=remaining)

    return {
        "alert_level": level,
        "message": msg,
        "speech": msg,                      # send straight to text-to-speech
        "lang": lang,
        "vibration": VIBRATION[level],      # haptic pattern in ms for the phone
        "urgent": level in ("next_stop", "arrived", "missed"),
        "current_stop": {"id": cur["id"], "name": cur["name"], "distance_m": round(dist_cur)},
        "at_stop": dist_cur <= STOP_RADIUS_M,
        "next_stop": next_stop,
        "stops_remaining": remaining,
        "distance_to_destination_m": round(dist_dest),
        "off_route": dist_cur > OFF_ROUTE_M,
    }
