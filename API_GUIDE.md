# SmartBus Assist - API Guide (for Frontend and OCR/AI teammates)

Base URL: `http://<server-ip>:5000` (use your laptop's IP on the same Wi-Fi when testing on a phone).
All responses are JSON. Errors look like `{"error": "message"}` with status 400/404/409.

## The 3 rules
1. **Language:** add `lang=en|kn|hi` to any request (query string or JSON body). Default `en`.
2. **Speak `speech`:** every important response has a `speech` field. Pass it straight to text-to-speech.
   (Android: TextToSpeech, set locale `kn-IN` / `hi-IN` / `en-IN`. Web: `speechSynthesis.speak`.)
3. **Vibrate `vibration`:** it is a list of milliseconds `[vibrate, pause, vibrate, ...]`.
   (Android: `Vibrator.vibrate(VibrationEffect.createWaveform(...))`. Web: `navigator.vibrate(list)`.)
   Meanings: `[200]` approaching, `[300,150,300]` next stop / board OK, `[500,200,500,200,500]` arrived,
   `[1000,300,1000]` missed stop, `[800,200,800,200,800]` SOS sent, `[150,100,150]` could not read bus.

Stops can be given as an id, English name, Kannada name or Hindi name. Partial names work.

## Journey flow
```
1  User speaks destination    -> GET  /api/search
2  At the stop, camera reads  -> POST /api/assist/identify-bus
3  User boards                -> POST /api/trips
4  Every 3-5 s while riding   -> POST /api/trips/<id>/location   (speak + vibrate the reply)
5  Any time (big SOS button)  -> POST /api/sos
```

## 1. Search a route
`GET /api/search?from=Majestic&to=Whitefield&lang=kn`
GPS instead of a name for the start: `from_lat=12.97&from_lng=77.57`. Optional: `max_transfers` (0-3), `limit`.
```json
{ "found": true, "lang": "en",
  "from": {"id": 1, "name": "Majestic"}, "to": {"id": 8, "name": "Whitefield"},
  "speech": "Bus 335E goes directly from Majestic to Whitefield. Take bus 335E ...",
  "best": { "...same shape as one item below..." },
  "direct_buses":    [ {"type":"direct","buses":["335E"],"total_stops":6,"total_minutes":79,
                         "transfers":0,"transfer_points":[],"speech":"...","instructions":["..."],
                         "legs":[{"bus_number":"335E","board_at":"Majestic","get_off_at":"Whitefield",
                                  "num_stops":6,"minutes":79,"stops":[{"id":1,"name":"Majestic"}, ...]}]} ],
  "transfer_routes": [ {"type":"1-transfer","buses":["MH1","335E"],"transfer_points":["Marathahalli"], ...} ] }
```
Read `speech` for the best option. Let the user say "next option" to hear `transfer_routes[i].speech`.
`GET /api/transfers?from=&to=` returns only routes that need a bus change.

## 2. Identify the bus (OCR/AI teammate: send the text you read from the bus board)
`POST /api/assist/identify-bus`
```json
{ "detected_text": "335 E", "destination": "Whitefield", "lat": 12.9767, "lng": 77.5713, "lang": "en" }
```
Only `detected_text` is required. Spaces, dashes, lower case and look-alike characters (O/0, I/1, S/5, B/8)
are tolerated. Response:
```json
{ "identified": true, "confidence": 1.0, "bus_number": "335E", "route_name": "Majestic - Whitefield",
  "route_ends": ["Majestic","Whitefield"], "should_board": true,
  "speech": "This is bus 335E, running between Majestic and Whitefield. It goes to Whitefield. You can board.",
  "vibration": [300,150,300] }
```
- `should_board` is `false` if the bus does not go there or runs the opposite way; then `alternative` holds a better journey.
- `identified: false` means the text matched no bus; speak `speech` and ask the user to point the camera again.
- Tip for the OCR side: send the best guess even if unsure; the backend checks it against the real bus list.
  Low confidence (< 0.8) adds "Please confirm" to `speech`.

## 3. Start a trip
`POST /api/trips`  `{"bus_number":"335E","destination":"Marathahalli","boarding_stop":"Majestic"}`
(or `lat`/`lng` instead of `boarding_stop`). Returns `{"trip_id": 1, "direction": "forward", ...}`.

## 4. Live alerts
`POST /api/trips/1/location`  `{"lat":12.9784,"lng":77.6408,"lang":"en"}`
```json
{ "alert_level": "approaching", "speech": "Marathahalli is 2 stops away.", "vibration": [200],
  "urgent": false, "at_stop": true, "current_stop": {"id":5,"name":"Indiranagar","distance_m":0},
  "next_stop": "Domlur", "stops_remaining": 2, "distance_to_destination_m": 6958,
  "off_route": false, "trip_status": "active" }
```
`alert_level`: `on_route` -> `approaching` (2 stops) -> `next_stop` (1 stop) -> `arrived`, or `missed`.
Speak when `alert_level` changes (do not repeat `on_route` every poll). Speak `urgent: true` alerts immediately.
`trip_status` becomes `completed` on `arrived`/`missed`; stop polling then.

## 5. SOS
`POST /api/sos` `{"lat":12.977,"lng":77.5715,"lang":"en"}`
Returns `message_to_send` (SMS text with place and map link), `contacts`, `speech`, `vibration`.
The phone app sends the SMS/makes the call; the backend only logs it and builds the message.
Contacts: `GET/POST /api/contacts` (`{"name","phone","relation"}`), `DELETE /api/contacts/<id>`.

## Other endpoints
| Endpoint | Use |
|---|---|
| `POST /api/gps/detect` `{lat,lng}` | "Which stop am I at?" - returns `at_stop` (within 100 m) + buses there |
| `GET /api/gps/nearest?lat=&lng=&radius=` | Nearby stops |
| `GET /api/stops?q=` , `GET /api/stops/<id>/buses` | Stop list / buses at a stop |
| `GET /api/buses` , `GET /api/buses/<number>` | Bus list / full route |
| `POST /api/buses`, `DELETE /api/buses/<number>` | Admin: add/remove a bus |
| `GET /api/health` | Check the server is up |
