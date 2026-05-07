"""
Test core — eseguibili senza BlueStacks (nessun hardware richiesto).
Run: pytest tests/ -v
Run (solo puri): pytest tests/ -v -m "not hardware"
"""

import numpy as np
import pytest

from config import LOOP_INTERVAL, STUCK_FRAMES, TIMING_JITTER_PCT
from game_state import FrameState
from randomizer import jittered_interval, noisy_direction
from state_machine import StateMachine
from utils.geometry import distance, normalize, rotate

# ── Fake controller ────────────────────────────────────────────────────────────

class FakeCtrl:
    def __init__(self):
        self.moves = []
        self.stops = 0

    def move(self, dx, dy):
        self.moves.append((dx, dy))

    def stop(self):
        self.stops += 1


FRAME = np.zeros((600, 800, 3), dtype=np.uint8)


# ── FrameState ─────────────────────────────────────────────────────────────────

def test_framestate_defaults():
    s = FrameState()
    assert s.poison is False
    assert s.afk is False
    assert s.in_bush is False
    assert s.dist_to_bush == float("inf")
    assert s.nearest_bush_dir is None


def test_framestate_frozen():
    s = FrameState(poison=True)
    with pytest.raises(Exception):
        s.poison = False


# ── StateMachine stati ─────────────────────────────────────────────────────────

def test_fleeing_on_poison():
    sm = StateMachine()
    fc = FakeCtrl()
    s = FrameState(poison=True, nearest_bush_dir=(1.0, 0.0), dist_to_bush=100.0)
    result = sm.tick(FRAME, s, fc)
    assert result == "FLEEING"
    assert len(fc.moves) == 1


def test_fleeing_on_afk():
    sm = StateMachine()
    fc = FakeCtrl()
    s = FrameState(afk=True, nearest_bush_dir=(0.0, -1.0), dist_to_bush=50.0)
    result = sm.tick(FRAME, s, fc)
    assert result == "FLEEING"


def test_hiding_in_bush():
    sm = StateMachine()
    fc = FakeCtrl()
    s = FrameState(in_bush=True, nearest_bush_dir=(0.5, 0.5), dist_to_bush=3.0)
    result = sm.tick(FRAME, s, fc)
    assert result == "HIDING"


def test_moving_toward_bush():
    sm = StateMachine()
    fc = FakeCtrl()
    s = FrameState(nearest_bush_dir=(0.7, 0.7), dist_to_bush=200.0)
    result = sm.tick(FRAME, s, fc)
    assert result == "MOVING"
    assert len(fc.moves) == 1


def test_waiting_no_bush():
    sm = StateMachine()
    fc = FakeCtrl()
    s = FrameState(nearest_bush_dir=None, dist_to_bush=float("inf"))
    result = sm.tick(FRAME, s, fc)
    assert result == "WAITING"
    assert fc.stops >= 1


def test_hiding_when_close_to_bush():
    sm = StateMachine()
    fc = FakeCtrl()
    s = FrameState(nearest_bush_dir=(1.0, 0.0), dist_to_bush=5.0)  # < BUSH_REACH_DIST=8
    result = sm.tick(FRAME, s, fc)
    assert result == "HIDING"


# ── Stuck detection ────────────────────────────────────────────────────────────

def test_stuck_accumulates_on_static_frame():
    sm = StateMachine()
    s = FrameState(nearest_bush_dir=(1.0, 0.0), dist_to_bush=50.0)
    for _ in range(STUCK_FRAMES + 1):
        sm.update_stuck(FRAME, s)
    assert sm.stuck_count >= STUCK_FRAMES


def test_stuck_resets_on_flee():
    sm = StateMachine()
    sm.stuck_count = 10
    s = FrameState(poison=True, nearest_bush_dir=(1.0, 0.0), dist_to_bush=50.0)
    sm.update_stuck(FRAME, s)
    assert sm.stuck_count == 0


def test_stuck_no_direction_no_avoidance():
    sm = StateMachine()
    sm.stuck_count = 10
    s = FrameState(nearest_bush_dir=None, dist_to_bush=float("inf"))
    d = sm.choose_direction(s)
    assert d is None


# ── Randomizer ─────────────────────────────────────────────────────────────────

def test_jitter_within_bounds():
    lo = LOOP_INTERVAL * (1 - TIMING_JITTER_PCT)
    hi = LOOP_INTERVAL * (1 + TIMING_JITTER_PCT)
    for _ in range(500):
        v = jittered_interval()
        assert lo <= v <= hi, f"jitter fuori bounds: {v}"


def test_noisy_direction_normalized():
    for _ in range(100):
        dx, dy = noisy_direction(1.0, 0.0)
        mag = (dx**2 + dy**2) ** 0.5
        assert abs(mag - 1.0) < 0.001


def test_noisy_direction_zero_input():
    dx, dy = noisy_direction(0.0, 0.0)
    assert dx == 0.0 and dy == 0.0


# ── Geometry ───────────────────────────────────────────────────────────────────

def test_rotate_90():
    rx, ry = rotate(1.0, 0.0, 90.0)
    assert abs(rx) < 1e-6
    assert abs(ry - 1.0) < 1e-6


def test_rotate_180():
    rx, ry = rotate(1.0, 0.0, 180.0)
    assert abs(rx + 1.0) < 1e-6
    assert abs(ry) < 1e-6


def test_normalize_zero():
    assert normalize(0.0, 0.0) == (0.0, 0.0)


def test_normalize_unit():
    nx, ny = normalize(3.0, 4.0)
    assert abs(nx - 0.6) < 1e-6
    assert abs(ny - 0.8) < 1e-6


def test_distance_345():
    assert distance(0, 0, 3, 4) == 5.0


def test_distance_zero():
    assert distance(5, 5, 5, 5) == 0.0


# ── Edge cases ─────────────────────────────────────────────────────────────────

def test_tiny_frame_no_crash():
    sm = StateMachine()
    fc = FakeCtrl()
    tiny = np.zeros((50, 50, 3), dtype=np.uint8)
    s = FrameState(nearest_bush_dir=(1.0, 0.0), dist_to_bush=50.0)
    sm.tick(tiny, s, fc)  # non deve crashare


def test_zero_direction_frame():
    sm = StateMachine()
    fc = FakeCtrl()
    s = FrameState(nearest_bush_dir=(0.0, 0.0), dist_to_bush=0.0)
    sm.tick(FRAME, s, fc)  # non deve crashare
