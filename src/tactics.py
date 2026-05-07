from __future__ import annotations

import math
from abc import ABC, abstractmethod

from config import PLAYER_CENTER_X, PLAYER_CENTER_Y
from game_state import FrameState

_THREAT_POISON_WEIGHT = 0.40
_THREAT_ENEMY_WEIGHT  = 0.30
_THREAT_DIST_WEIGHT   = 0.30
_ENEMY_MAX_DIST       = 400.0
_ENEMY_COUNT_MAX      = 3


def compute_threat(state: FrameState, frame_w: int, frame_h: int) -> float:
    """Enemy threat level 0.0 (safe) → 1.0 (critical)."""
    threat = 0.0

    if state.poison:
        threat += _THREAT_POISON_WEIGHT

    if not state.enemies:
        return min(1.0, threat)

    px = frame_w * PLAYER_CENTER_X
    py = frame_h * PLAYER_CENTER_Y

    n = len(state.enemies)
    threat += _THREAT_ENEMY_WEIGHT * min(1.0, n / _ENEMY_COUNT_MAX)

    min_dist = min(math.hypot(ex - px, ey - py) for ex, ey in state.enemies)
    if min_dist < _ENEMY_MAX_DIST:
        threat += _THREAT_DIST_WEIGHT * (1.0 - min_dist / _ENEMY_MAX_DIST)

    return min(1.0, threat)


class Tactic(ABC):
    priority: int = 0

    @abstractmethod
    def should_activate(self, state: FrameState, threat: float) -> bool: ...

    @abstractmethod
    def tactic_name(self) -> str: ...

    def direction(
        self, state: FrameState, frame_w: int, frame_h: int
    ) -> tuple[float, float] | None:
        return state.nearest_bush_dir


class FleePoisonTactic(Tactic):
    priority = 100

    def should_activate(self, state: FrameState, threat: float) -> bool:
        return state.poison or state.afk

    def tactic_name(self) -> str:
        return "FLEE_POISON"


class AvoidEnemyTactic(Tactic):
    priority  = 80
    THRESHOLD = 0.5

    def should_activate(self, state: FrameState, threat: float) -> bool:
        return threat >= self.THRESHOLD and not state.in_bush

    def tactic_name(self) -> str:
        return "AVOID_ENEMY"

    def direction(
        self, state: FrameState, frame_w: int, frame_h: int
    ) -> tuple[float, float] | None:
        if not state.enemies:
            return state.nearest_bush_dir

        px = frame_w * PLAYER_CENTER_X
        py = frame_h * PLAYER_CENTER_Y
        nearest = min(state.enemies, key=lambda e: math.hypot(e[0] - px, e[1] - py))
        ex, ey   = nearest
        dx, dy   = px - ex, py - ey
        dist     = math.hypot(dx, dy)
        if dist < 1.0:
            return state.nearest_bush_dir

        flee = (dx / dist, dy / dist)
        if state.nearest_bush_dir:
            bx, by = state.nearest_bush_dir
            rx = 0.6 * flee[0] + 0.4 * bx
            ry = 0.6 * flee[1] + 0.4 * by
            norm = math.hypot(rx, ry)
            if norm > 0:
                return (rx / norm, ry / norm)
        return flee


class HideInBushTactic(Tactic):
    priority = 50

    def should_activate(self, state: FrameState, threat: float) -> bool:
        return not state.in_bush and state.nearest_bush_dir is not None

    def tactic_name(self) -> str:
        return "HIDE_IN_BUSH"


class PatrolTactic(Tactic):
    priority = 10

    def should_activate(self, state: FrameState, threat: float) -> bool:
        return True  # always-on fallback

    def tactic_name(self) -> str:
        return "PATROL"


_SORTED_TACTICS: list[Tactic] = sorted(
    [FleePoisonTactic(), AvoidEnemyTactic(), HideInBushTactic(), PatrolTactic()],
    key=lambda t: t.priority,
    reverse=True,
)


class TacticSelector:
    def select(
        self,
        state: FrameState,
        threat: float,
        frame_w: int,
        frame_h: int,
    ) -> tuple[Tactic, tuple[float, float] | None]:
        for tactic in _SORTED_TACTICS:
            if tactic.should_activate(state, threat):
                return tactic, tactic.direction(state, frame_w, frame_h)
        return _SORTED_TACTICS[-1], state.nearest_bush_dir
