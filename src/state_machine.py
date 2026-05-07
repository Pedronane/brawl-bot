from __future__ import annotations

import time

import numpy as np

from config import (
    AVOID_ANGLE,
    BACKUP_FRAMES,
    BUSH_REACH_DIST,
    COMMIT_FRAMES,
    STUCK_DIFF,
    STUCK_FRAMES,
    WIGGLE_DURATION,
    WIGGLE_INTERVAL,
)
from game_state import FrameState
from randomizer import noisy_direction
from tactics import get_tactics
from utils.geometry import rotate

_WIGGLE_DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


class StateMachine:
    def __init__(self) -> None:
        self.prev_state: str = ""
        self.wiggle_counter: int = 0
        self.wiggle_step: int = 0
        self.prev_roi: np.ndarray | None = None
        self.stuck_count: int = 0
        self.deflect_sign: int = 1
        self.commit_left: int = 0
        self.avoid_phase: int = 0
        self._backup_dir: tuple[float, float] | None = None
        self._deviated: tuple[float, float] | None = None
        self.total_stuck: int = 0

        # Hysteresis tracking
        self._is_fleeing: bool = False
        self._is_engaging: bool = False

    # ── Stuck detection ────────────────────────────────────────────────────────

    def _center_roi(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        m = 38
        return frame[h // 2 - m:h // 2 + m, w // 2 - m:w // 2 + m].copy()

    def update_stuck(self, frame: np.ndarray, state: FrameState) -> bool:
        """Aggiorna stuck detection. Ritorna True se stuck questo frame."""
        roi = self._center_roi(frame)
        flee_active = state.poison or state.afk

        if self.prev_roi is not None and self.prev_roi.shape == roi.shape and not flee_active:
            diff = np.mean(np.abs(roi.astype(float) - self.prev_roi.astype(float)))
            moving = not (state.in_bush and not state.poison and not state.afk)
            if moving and self.commit_left == 0 and diff < STUCK_DIFF:
                self.stuck_count += 1
                self.total_stuck += 1
            else:
                self.stuck_count = 0
        elif flee_active:
            self.stuck_count = 0
            self.commit_left = 0

        self.prev_roi = roi
        return self.stuck_count >= STUCK_FRAMES

    def choose_direction(self, state: FrameState) -> tuple[float, float] | None:
        """Wall avoidance + committed sequence. Ritorna direzione effettiva."""
        direction = state.nearest_bush_dir

        if self.stuck_count >= STUCK_FRAMES and self.commit_left == 0 and direction:
            self.commit_left = BACKUP_FRAMES + COMMIT_FRAMES
            self.avoid_phase = 0
            self.stuck_count = 0
            self._backup_dir = (-direction[0], -direction[1])
            self._deviated = rotate(*direction, AVOID_ANGLE * self.deflect_sign)
            self.deflect_sign *= -1

        if self.commit_left > 0:
            self.commit_left -= 1
            if self.avoid_phase == 0 and self.commit_left <= COMMIT_FRAMES:
                self.avoid_phase = 1
            return self._backup_dir if self.avoid_phase == 0 else self._deviated

        return direction

    # ── Decision helpers ───────────────────────────────────────────────────────

    def _should_flee(self, state: FrameState, tactics: dict) -> bool:
        """True se dobbiamo fuggire — con isteresi."""
        if state.poison or state.afk:
            return True
        if state.hp_ratio <= 0.0:
            return False   # sconosciuto → non fuggire
        flee_hp = tactics["flee_hp"]
        hysteresis = tactics.get("flee_hp_hysteresis", 0.10)
        if self._is_fleeing:
            # Uscita da FLEEING solo se HP recuperata sopra soglia+hysteresis
            return state.hp_ratio < flee_hp + hysteresis
        return state.hp_ratio < flee_hp

    def _should_engage(self, state: FrameState, tactics: dict) -> bool:
        """True se condizioni per ingaggiare un nemico sono soddisfatte."""
        if not state.enemies:
            return False
        if self._is_fleeing:
            return False   # mai ingaggiare mentre si fugge
        engage_hp = tactics.get("engage_hp", 0.70)
        engage_threshold = tactics.get("engage_threshold", 2)
        hp_ok = state.hp_ratio >= engage_hp
        cubes_ok = state.cubes_self >= engage_threshold
        return hp_ok and cubes_ok

    # ── Main tick ──────────────────────────────────────────────────────────────

    def tick(self, frame: np.ndarray, state: FrameState, controller) -> str:
        """Esegui un frame della state machine. Ritorna nome stato corrente."""
        tactics = get_tactics(state.game_phase)
        self.update_stuck(frame, state)
        effective_dir = self.choose_direction(state)

        # ── 1. FLEEING — massima priorità ─────────────────────────────────────
        if self._should_flee(state, tactics) and effective_dir:
            self._is_fleeing = True
            self._is_engaging = False
            noisy = noisy_direction(*effective_dir)
            controller.move(*noisy)
            self.wiggle_counter = 0
            return "FLEEING"

        # Uscita da FLEEING
        if self._is_fleeing and not state.poison and not state.afk:
            flee_exit_hp = tactics["flee_hp"] + tactics.get("flee_hp_hysteresis", 0.10)
            if state.hp_ratio <= 0.0 or state.hp_ratio >= flee_exit_hp:
                self._is_fleeing = False

        # ── 2. ENGAGING — priorità alta se condizioni soddisfatte ─────────────
        if self._should_engage(state, tactics):
            self._is_engaging = True
            controller.stop()   # hold position — aim assist aggiunto in Fase 3
            return "ENGAGING"

        if self._is_engaging and not state.enemies:
            self._is_engaging = False

        # ── 3. HIDING — in cespuglio ──────────────────────────────────────────
        if state.in_bush and not state.poison and not state.afk:
            self.wiggle_counter += 1
            max_wait = tactics.get("bush_wait_max", WIGGLE_INTERVAL)
            if self.wiggle_counter >= max_wait:
                d = _WIGGLE_DIRS[self.wiggle_step % len(_WIGGLE_DIRS)]
                controller.move(*d)
                time.sleep(WIGGLE_DURATION)
                controller.stop()
                self.wiggle_step += 1
                self.wiggle_counter = 0
            else:
                controller.stop()
            return "HIDING"

        # ── 4. MOVING — verso cespuglio ───────────────────────────────────────
        if effective_dir and state.dist_to_bush > BUSH_REACH_DIST:
            noisy = noisy_direction(*effective_dir)
            controller.move(*noisy)
            return "MOVING"

        # ── 5. HIDING — vicino al cespuglio ───────────────────────────────────
        if effective_dir:
            controller.stop()
            return "HIDING"

        # ── 6. WAITING — nessuna direzione disponibile ────────────────────────
        controller.stop()
        return "WAITING"
