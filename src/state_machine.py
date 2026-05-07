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
from tactics import TacticSelector, compute_threat
from utils.geometry import rotate

_WIGGLE_DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


class StateMachine:
    def __init__(self):
        self.prev_state     = ""
        self.wiggle_counter = 0
        self.wiggle_step    = 0
        self.prev_roi       = None
        self.stuck_count    = 0
        self.deflect_sign   = 1
        self.commit_left    = 0
        self.avoid_phase    = 0
        self._backup_dir    = None
        self._deviated      = None
        self.total_stuck    = 0
        self._tactic_sel    = TacticSelector()

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

    def _resolve_direction(
        self,
        state: FrameState,
        tactic_dir: tuple[float, float] | None,
    ) -> tuple[float, float] | None:
        """Wall avoidance trumps tactic direction when active."""
        direction = state.nearest_bush_dir

        if self.stuck_count >= STUCK_FRAMES and self.commit_left == 0 and direction:
            self.commit_left  = BACKUP_FRAMES + COMMIT_FRAMES
            self.avoid_phase  = 0
            self.stuck_count  = 0
            self._backup_dir  = (-direction[0], -direction[1])
            self._deviated    = rotate(*direction, AVOID_ANGLE * self.deflect_sign)
            self.deflect_sign *= -1

        if self.commit_left > 0:
            self.commit_left -= 1
            if self.avoid_phase == 0 and self.commit_left <= COMMIT_FRAMES:
                self.avoid_phase = 1
            return self._backup_dir if self.avoid_phase == 0 else self._deviated

        return tactic_dir

    def tick(self, frame: np.ndarray, state: FrameState, controller) -> str:
        """Esegui un frame. Ritorna nome stato corrente."""
        self.update_stuck(frame, state)

        frame_h, frame_w = frame.shape[:2]
        threat = compute_threat(state, frame_w, frame_h)
        tactic, tactic_dir = self._tactic_sel.select(state, threat, frame_w, frame_h)
        effective_dir = self._resolve_direction(state, tactic_dir)

        if (state.poison or state.afk) and effective_dir:
            controller.move(*noisy_direction(*effective_dir))
            self.wiggle_counter = 0
            return "FLEEING"

        if tactic.tactic_name() == "AVOID_ENEMY" and effective_dir and not state.in_bush:
            controller.move(*noisy_direction(*effective_dir))
            self.wiggle_counter = 0
            return "ENGAGING"

        if state.in_bush and not state.poison and not state.afk:
            self.wiggle_counter += 1
            if self.wiggle_counter >= WIGGLE_INTERVAL:
                d = _WIGGLE_DIRS[self.wiggle_step % len(_WIGGLE_DIRS)]
                controller.move(*d)
                time.sleep(WIGGLE_DURATION)
                controller.stop()
                self.wiggle_step    += 1
                self.wiggle_counter  = 0
            else:
                controller.stop()
            return "HIDING"

        if effective_dir and state.dist_to_bush > BUSH_REACH_DIST:
            controller.move(*noisy_direction(*effective_dir))
            return "MOVING"

        if effective_dir:
            controller.stop()
            return "HIDING"

        controller.stop()
        return "WAITING"
