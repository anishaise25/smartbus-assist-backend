"""Database layer (SQLite). Tables: stops, buses, route_stops, trips."""
import os
import sqlite3

DEFAULT_DB = os.environ.get("BUS_DB", os.path.join(os.path.dirname(__file__), "buses.db"))

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS stops (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    lat  REAL NOT NULL,
    lng  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS buses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    number        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name          TEXT,
    bus_type      TEXT DEFAULT 'Ordinary',
    bidirectional INTEGER NOT NULL DEFAULT 1   -- 1 = runs both ways along the route
);

-- Optional translated stop names (lang = 'kn' or 'hi'); falls back to English
CREATE TABLE IF NOT EXISTS stop_names (
    stop_id INTEGER NOT NULL REFERENCES stops(id) ON DELETE CASCADE,
    lang    TEXT NOT NULL,
    name    TEXT NOT NULL,
    PRIMARY KEY (stop_id, lang)
);

-- Ordered list of stops for each bus (seq starts at 1)
CREATE TABLE IF NOT EXISTS route_stops (
    bus_id  INTEGER NOT NULL REFERENCES buses(id) ON DELETE CASCADE,
    stop_id INTEGER NOT NULL REFERENCES stops(id),
    seq     INTEGER NOT NULL,
    PRIMARY KEY (bus_id, seq),
    UNIQUE (bus_id, stop_id)
);
CREATE INDEX IF NOT EXISTS idx_route_stops_stop ON route_stops(stop_id);

-- A passenger's live journey, used for GPS alerts
CREATE TABLE IF NOT EXISTS trips (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bus_id          INTEGER NOT NULL REFERENCES buses(id),
    board_stop_id   INTEGER NOT NULL REFERENCES stops(id),
    dest_stop_id    INTEGER NOT NULL REFERENCES stops(id),
    direction       INTEGER NOT NULL,           -- +1 forward, -1 reverse along route
    status          TEXT NOT NULL DEFAULT 'active',  -- active | completed
    last_stop_id    INTEGER,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Trusted people notified in an emergency
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    phone TEXT NOT NULL,
    relation TEXT
);

CREATE TABLE IF NOT EXISTS sos_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    lat        REAL NOT NULL,
    lng        REAL NOT NULL,
    trip_id    INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect(path=None):
    conn = sqlite3.connect(path or DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path=None):
    conn = connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
