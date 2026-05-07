"""Schema SQLite per metriche bot — matches, state_transitions, detections_sample."""
from __future__ import annotations

import sqlite3
from pathlib import Path

_DDL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS matches (
    match_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_start        TEXT NOT NULL,
    ts_end          TEXT,
    duration_sec    INTEGER,
    placement       INTEGER,
    trophies_delta  INTEGER,
    death_cause     TEXT,               -- 'poison' | 'player' | 'survived' | 'unknown'
    cubes_collected INTEGER DEFAULT 0,
    game_phase_end  TEXT,               -- fase in cui è morto
    policy_variant  TEXT DEFAULT 'default'
);

CREATE TABLE IF NOT EXISTS state_transitions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    match_id    INTEGER REFERENCES matches(match_id),
    from_state  TEXT NOT NULL,
    to_state    TEXT NOT NULL,
    trigger     TEXT,
    hp_ratio    REAL,
    players_left INTEGER,
    poison_phase TEXT,
    frame_idx   INTEGER
);

CREATE TABLE IF NOT EXISTS detections_sample (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    match_id        INTEGER REFERENCES matches(match_id),
    frame_idx       INTEGER,
    enemies_count   INTEGER DEFAULT 0,
    players_left    INTEGER DEFAULT 0,
    hp_ratio        REAL    DEFAULT 1.0,
    poison_progress REAL    DEFAULT 0.0,
    in_bush         INTEGER DEFAULT 0,
    afk_warning     INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_transitions_match ON state_transitions(match_id);
CREATE INDEX IF NOT EXISTS idx_detections_match  ON detections_sample(match_id);
"""


def open_db(db_path: Path | str) -> sqlite3.Connection:
    """Apre (o crea) il DB SQLite con schema corretto. Ritorna connessione."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.executescript(_DDL)
    conn.commit()
    return conn
