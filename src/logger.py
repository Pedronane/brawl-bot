from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger as _logger

_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_logger.remove()
_logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | {message}",
    level="INFO",
    colorize=True,
)
_logger.add(
    _LOG_DIR / "bot_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <7} | {message}",
    level="DEBUG",
    rotation="00:00",
    retention=10,
    encoding="utf-8",
)

log = _logger


# ── SQLite session logger ──────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SessionLogger:
    """Scrive metriche di sessione su SQLite. Thread-safe (lock interno sqlite3)."""

    def __init__(self, conn: sqlite3.Connection, policy_variant: str = "default") -> None:
        self._conn = conn
        self._policy = policy_variant
        self._match_id: int | None = None
        self._match_start: str | None = None
        self._sample_counter = 0
        self._sample_every = 30       # scrivi sample ogni N frame (~1 Hz a 30 FPS)
        self._prev_state: str = ""

    # ── Match lifecycle ────────────────────────────────────────────────────────

    def match_start(self) -> None:
        self._match_start = _now()
        cur = self._conn.execute(
            "INSERT INTO matches (ts_start, policy_variant) VALUES (?, ?)",
            (self._match_start, self._policy),
        )
        self._conn.commit()
        self._match_id = cur.lastrowid
        log.debug(f"[DB] match_start id={self._match_id}")

    def match_end(
        self,
        placement: int | None = None,
        trophies_delta: int | None = None,
        death_cause: str = "unknown",
        cubes_collected: int = 0,
        game_phase_end: str = "UNKNOWN",
    ) -> None:
        if self._match_id is None:
            return
        ts_end = _now()
        duration = None
        if self._match_start:
            try:
                from datetime import datetime as dt
                start = dt.fromisoformat(self._match_start)
                end = dt.fromisoformat(ts_end)
                duration = int((end - start).total_seconds())
            except Exception:
                pass

        self._conn.execute(
            """UPDATE matches SET ts_end=?, duration_sec=?, placement=?,
               trophies_delta=?, death_cause=?, cubes_collected=?, game_phase_end=?
               WHERE match_id=?""",
            (ts_end, duration, placement, trophies_delta,
             death_cause, cubes_collected, game_phase_end, self._match_id),
        )
        self._conn.commit()
        log.debug(f"[DB] match_end id={self._match_id} placement={placement} cause={death_cause}")
        self._match_id = None

    # ── State transitions ──────────────────────────────────────────────────────

    def log_transition(
        self,
        from_state: str,
        to_state: str,
        trigger: str = "",
        hp_ratio: float = 1.0,
        players_left: int = 0,
        poison_phase: str = "UNKNOWN",
        frame_idx: int = 0,
    ) -> None:
        if from_state == to_state:
            return
        self._conn.execute(
            """INSERT INTO state_transitions
               (ts, match_id, from_state, to_state, trigger,
                hp_ratio, players_left, poison_phase, frame_idx)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (_now(), self._match_id, from_state, to_state, trigger,
             hp_ratio, players_left, poison_phase, frame_idx),
        )
        self._conn.commit()

    # ── Periodic detections sample ─────────────────────────────────────────────

    def maybe_sample(self, frame_state) -> None:
        """Chiama ogni frame. Scrive su DB solo ogni self._sample_every frame."""
        self._sample_counter += 1
        if self._sample_counter % self._sample_every != 0:
            return
        self._conn.execute(
            """INSERT INTO detections_sample
               (ts, match_id, frame_idx, enemies_count, players_left,
                hp_ratio, poison_progress, in_bush, afk_warning)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                _now(),
                self._match_id,
                getattr(frame_state, "frame_idx", 0),
                len(getattr(frame_state, "enemies", ())),
                getattr(frame_state, "players_left", 0),
                getattr(frame_state, "hp_ratio", 1.0),
                getattr(frame_state, "poison_progress", 0.0),
                int(getattr(frame_state, "in_bush", False)),
                int(getattr(frame_state, "afk", False)),
            ),
        )
        self._conn.commit()
