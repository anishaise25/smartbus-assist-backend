# SmartBus Assist - AI-Based Bus Route Detection for Visually Impaired
## Backend (Member 2)

Flask + SQLite. Run:

    pip install -r requirements.txt
    python app.py            # http://localhost:5000  (DB auto-created and seeded)
    python test_api.py       # self-tests

Seed data is illustrative (Bengaluru-style). Replace `seed_data.py` with real BMTC data, or load it via the APIs.

## Files
| File | Purpose |
|---|---|
| db.py | Schema: stops, buses, route_stops (ordered), trips |
| seed_data.py | Sample stops, buses, routes |
| routes_logic.py | Stop lookup, direct search, transfers (up to 3), ranking |
| gps.py | Haversine, nearest-stop detection, trip alert logic |
| speech.py / voice.py / i18n.py | Bus-number matching, spoken sentences, en/kn/hi text |
| import_data.py | Load GTFS/CSV data |
| demo.py | Presentation demo |
| app.py | Flask APIs |

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/stops?q= | List/search stops |
| POST | /api/stops | Add stop `{name,lat,lng}` |
| GET | /api/stops/<id>/buses | Buses serving a stop |
| GET | /api/buses | All buses |
| GET | /api/buses/<number> | Route details (ordered stops) |
| POST | /api/buses | Add bus `{number,name,bus_type,bidirectional,stops:[...]}` |
| DELETE | /api/buses/<number> | Remove bus |
| GET | /api/search?from=&to= | Direct buses + alternatives + transfers |
| GET | /api/search?from_lat=&from_lng=&to= | Same, source taken from GPS |
| GET | /api/transfers?from=&to= | Only routes needing a bus change |
| GET | /api/gps/nearest?lat=&lng=&radius= | Nearest stops |
| POST | /api/gps/detect `{lat,lng}` | At a stop? + buses there |
| POST | /api/trips `{bus_number,destination,boarding_stop or lat/lng}` | Start tracking |
| POST | /api/trips/<id>/location `{lat,lng}` | Send GPS; get alert |

`from`/`to` accept a stop id or a name (case-insensitive, partial OK).
Alert levels: `on_route`, `approaching`, `next_stop`, `arrived`, `missed`.

## Example
    curl "localhost:5000/api/search?from=Banashankari&to=Whitefield"
    -> best: Board MH1 at Banashankari -> Marathahalli, change to 335E -> Whitefield

## Accessibility endpoints (voice-first)
| Method | Endpoint | Purpose |
|---|---|---|
| POST | /api/assist/identify-bus `{detected_text, destination?, lat?, lng?}` | Takes text the camera/OCR model read from a bus board (tolerates OCR errors like O/0, "335 E"); says which bus it is and whether to board |
| POST | /api/sos `{lat,lng,trip_id?}` | Logs emergency, returns message + contacts for the app to SMS/call |
| GET/POST/DELETE | /api/contacts | Manage emergency contacts |

Every search result, bus identification, trip alert and SOS response includes:
- `speech`: a sentence to pass straight to text-to-speech
- `vibration`: haptic pattern in ms (e.g. `[500,200,500,200,500]` = arrived)

Integration flow: camera model -> `identify-bus` -> user boards -> `POST /api/trips` -> app posts GPS every few seconds to `/api/trips/<id>/location` -> speaks `speech` and vibrates.

## Languages
Add `lang=en|kn|hi` to any request. Stop names can also be typed/spoken in Kannada or Hindi
(translated names live in the `stop_names` table). The kn/hi wording is in `i18n.py` - have a native speaker review it.

## Using real BMTC data
    python import_data.py gtfs path/to/bmtc_gtfs --replace [--max-routes 500]
    python import_data.py csv stops.csv routes.csv --replace      # templates: sample_data/
Unzip the GTFS feed first. Source: the community feed github.com/Vonter/bmtc-gtfs (gtfs/bmtc.zip, ~4,400 routes with full
stop lists) or the official feed on hub.tumidata.org. The official feed lists only start/end stops for many routes, so
the community feed is better for route search. Check licence/freshness. Translated stop names are not in these feeds:
add them with the CSV import or `stop_names` rows.

## More docs
- API_GUIDE.md - for frontend and OCR teammates
- DEMO_SCRIPT.md - presentation flow; `python demo.py --lang kn`

## How it works
- Search expands by number of buses used (0, 1, 2 transfers); transfers only at stops served by 2+ buses.
- Time = distance/18 km/h + 0.5 min per stop + 7 min wait per transfer; results ranked by time + transfer penalty.
- Buses are bidirectional by default; set `bidirectional: false` for one-way routes.
- GPS: stop detected within 100 m; alerts use stops remaining and distance to destination.
