# SmartBus Assist - Demo Script

Run `python demo.py` (add `--lang kn` or `--lang hi`). It uses a temporary database, so it is safe to run repeatedly.
For a live demo, start the server (`python app.py`) and call the endpoints from the app or `curl`.

## Suggested 6-minute flow
| Min | Scenario | What to say | What the audience sees/hears |
|---|---|---|---|
| 0-1 | Problem | Visually impaired commuters cannot read bus boards or know when to get down. | - |
| 1-2 | 1. Route planning | "She says: Majestic to Whitefield." | Spoken direct-bus answer |
| 2-3 | 2. Bus change | "No direct bus? The system suggests where to change." | Spoken change instructions (Banashankari -> Whitefield) |
| 3-4 | 3. Bus identification | "Camera reads the board. Even when it misreads 500D as 5OOD, the backend corrects it." | Right bus: board. Wrong bus: do not board + better bus. Blurry: ask again |
| 4-5 | 4. Live ride | "GPS tells her how many stops are left." | Alerts get more urgent with distance; vibrations differ by alert |
| 5-5.5 | 5. Missed stop | "If she misses it, she is told immediately." | Missed-stop alert |
| 5.5-6 | 6. SOS | "One button alerts her family with a map link." | SMS text with nearest stop |

Run the demo again in Kannada (`--lang kn`) to show local-language support.

## Likely questions
- **Where is the AI?** Bus-board reading (OCR/vision, by the camera module) plus the backend's error-tolerant matching and route recommendation.
- **Is the data real?** The built-in data is sample data. `import_data.py` loads the real BMTC GTFS feed.
- **How accurate is GPS?** Phone GPS is about 5-20 m; stop detection uses 100 m, and alerts use stop counts as well as distance.
- **What if there is no internet?** Currently the server needs a connection; offline mode is future work.
- **Privacy?** Location is used only during a trip and SOS; nothing is stored except SOS events.

## Limitations to state honestly
- Travel times are estimates (average speed), not live bus arrival times.
- Kannada and Hindi wording should be checked by native speakers.
- Real-time bus positions are not used; GPS is the passenger's phone.
