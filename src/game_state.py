from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple


class Enemy(NamedTuple):
    x: int
    y: int
    hp_ratio: float = 1.0       # frazione HP [0.0, 1.0] (1.0 = sconosciuto)
    confidence: float = 1.0     # score detection [0.0, 1.0]


@dataclass(frozen=True)
class FrameState:
    # ── Phase 0-1 (invariati) ──────────────────────────────────────────────────
    bushes: tuple = field(default_factory=tuple)      # ((cx, cy, area), ...)
    enemies: tuple = field(default_factory=tuple)     # (Enemy(...), ...)
    poison: bool = False
    afk: bool = False
    in_bush: bool = False
    stuck: bool = False
    nearest_bush_dir: tuple | None = None             # (dx, dy) normalizzato
    dist_to_bush: float = float("inf")
    frame_idx: int = 0

    # ── Phase 2 (nuovi) ───────────────────────────────────────────────────────
    players_left: int = 0           # giocatori rimasti (0 = sconosciuto)
    hp_ratio: float = 1.0           # propria HP [0.0, 1.0]
    cubes_self: int = 0             # Power Cubes posseduti
    poison_progress: float = 0.0   # avanzamento ring/zona [0.0, 1.0]
    game_phase: str = "UNKNOWN"     # "EARLY" | "MID" | "LATE" | "UNKNOWN"
