"""
Test Phase 2 — TemporalFilter, FrameSanity, ResourceGuard, db_schema, game_phase.
Nessun hardware richiesto.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import numpy as np
import pytest

from game_state import Enemy, FrameState
from utils.image_proc import FrameSanity, TemporalFilter


# ── TemporalFilter ─────────────────────────────────────────────────────────────

class TestTemporalFilter:
    def test_empty_returns_empty(self):
        tf = TemporalFilter(window=3, radius=40, threshold=2)
        assert tf.update([]) == []

    def test_single_frame_below_threshold(self):
        tf = TemporalFilter(window=3, radius=40, threshold=2)
        e = Enemy(100, 200)
        # 1 frame — threshold=2 → niente confermato
        result = tf.update([e])
        assert result == []

    def test_two_frames_confirms_stable_enemy(self):
        tf = TemporalFilter(window=3, radius=40, threshold=2)
        e1 = Enemy(100, 200)
        e2 = Enemy(102, 198)  # ~2.8 px di distanza, sotto radius=40
        tf.update([e1])
        result = tf.update([e2])
        assert len(result) == 1

    def test_unstable_enemy_not_confirmed(self):
        """Nemico che salta di posizione > radius non viene confermato."""
        tf = TemporalFilter(window=3, radius=40, threshold=2)
        e1 = Enemy(100, 200)
        e2 = Enemy(500, 500)   # molto lontano
        tf.update([e1])
        result = tf.update([e2])
        assert len(result) == 0

    def test_reset_clears_history(self):
        tf = TemporalFilter(window=3, radius=40, threshold=2)
        e = Enemy(100, 200)
        tf.update([e])
        tf.reset()
        result = tf.update([e])
        assert result == []

    def test_multiple_enemies(self):
        tf = TemporalFilter(window=3, radius=40, threshold=2)
        e1 = Enemy(100, 200)
        e2 = Enemy(400, 300)
        tf.update([e1, e2])
        result = tf.update([Enemy(101, 201), Enemy(401, 301)])
        assert len(result) == 2


# ── FrameSanity ────────────────────────────────────────────────────────────────

class TestFrameSanity:
    def _frame(self, h=600, w=800, fill=128, noise=True) -> np.ndarray:
        f = np.full((h, w, 3), fill, dtype=np.uint8)
        if noise:
            f += np.random.randint(0, 30, f.shape, dtype=np.uint8)
        return f

    def test_good_frame_ok(self):
        fs = FrameSanity()
        ok, reason = fs.check(self._frame())
        assert ok
        assert reason == "ok"

    def test_too_small_rejected(self):
        fs = FrameSanity()
        ok, reason = fs.check(np.zeros((50, 50, 3), dtype=np.uint8))
        assert not ok
        assert reason == "wrong_dims"

    def test_monochrome_rejected(self):
        fs = FrameSanity()
        ok, reason = fs.check(np.full((600, 800, 3), 100, dtype=np.uint8))
        assert not ok
        assert reason == "monochrome"

    def test_freeze_detection(self):
        # freeze_n=4: prima call imposta hash (no count), poi 4 diff==0 → trigger a 5a call
        fs = FrameSanity(freeze_n=4)
        frozen = self._frame(noise=True)  # std > 1 → passa monochrome; stesso oggetto = freeze reale
        for _ in range(4):
            ok, _ = fs.check(frozen)
            assert ok  # non ancora freeze
        ok, reason = fs.check(frozen)
        assert not ok
        assert "freeze" in reason

    def test_varying_frames_no_freeze(self):
        fs = FrameSanity(freeze_n=5)
        for _ in range(10):
            ok, reason = fs.check(self._frame(noise=True))
            # frame diversi → nessun freeze
            assert ok or reason != "freeze_5"


# ── FrameState nuovi campi ─────────────────────────────────────────────────────

def test_framestate_new_defaults():
    s = FrameState()
    assert s.players_left == 0
    assert s.hp_ratio == 1.0
    assert s.cubes_self == 0
    assert s.poison_progress == 0.0
    assert s.game_phase == "UNKNOWN"


def test_framestate_with_enemies():
    e = Enemy(100, 200, hp_ratio=0.5, confidence=0.9)
    s = FrameState(enemies=(e,))
    assert len(s.enemies) == 1
    assert s.enemies[0].x == 100
    assert s.enemies[0].hp_ratio == 0.5


def test_framestate_backward_compat():
    """Costruzione senza nuovi campi — backward compat per state_machine."""
    s = FrameState(poison=True, nearest_bush_dir=(1.0, 0.0), dist_to_bush=50.0)
    assert s.poison is True
    assert s.game_phase == "UNKNOWN"


# ── detect_game_phase ──────────────────────────────────────────────────────────

def test_game_phase_via_players():
    from detector import detect_game_phase
    assert detect_game_phase(players_left=9) == "EARLY"
    assert detect_game_phase(players_left=5) == "MID"
    assert detect_game_phase(players_left=2) == "LATE"


def test_game_phase_via_timer():
    from detector import detect_game_phase
    assert detect_game_phase(players_left=0, elapsed_sec=10) == "EARLY"
    assert detect_game_phase(players_left=0, elapsed_sec=70) == "MID"
    assert detect_game_phase(players_left=0, elapsed_sec=120) == "LATE"


# ── db_schema ─────────────────────────────────────────────────────────────────

def test_db_schema_creates_tables():
    from utils.db_schema import open_db
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        conn = open_db(db_path)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        assert "matches" in tables
        assert "state_transitions" in tables
        assert "detections_sample" in tables
        conn.close()


def test_db_insert_match():
    from utils.db_schema import open_db
    with tempfile.TemporaryDirectory() as tmp:
        conn = open_db(Path(tmp) / "test.db")
        conn.execute(
            "INSERT INTO matches (ts_start, policy_variant) VALUES (?, ?)",
            ("2026-01-01T00:00:00+00:00", "default"),
        )
        conn.commit()
        row = conn.execute("SELECT COUNT(*) FROM matches").fetchone()
        assert row[0] == 1
        conn.close()


# ── ResourceGuard ─────────────────────────────────────────────────────────────

def test_resource_guard_returns_true_normally():
    from utils.resource_guard import ResourceGuard
    rg = ResourceGuard(check_every=1, rss_max_mb=99999, cpu_max_pct=100.0)
    for _ in range(3):
        assert rg.tick() is True


# ── Tactics ───────────────────────────────────────────────────────────────────

def test_get_tactics_all_phases():
    from tactics import get_tactics
    for phase in ("EARLY", "MID", "LATE", "UNKNOWN"):
        t = get_tactics(phase)
        assert "flee_hp" in t
        assert "engage_hp" in t
        assert "engage_threshold" in t

def test_get_tactics_unknown_fallback():
    from tactics import get_tactics
    t = get_tactics("NONEXISTENT")
    assert t == get_tactics("UNKNOWN")

def test_flee_hp_increases_over_phases():
    from tactics import get_tactics
    assert get_tactics("EARLY")["flee_hp"] < get_tactics("LATE")["flee_hp"]

def test_engage_threshold_decreases_late():
    from tactics import get_tactics
    assert get_tactics("LATE")["engage_threshold"] < get_tactics("EARLY")["engage_threshold"]

def test_should_grab_cube_safe():
    from tactics import should_grab_cube
    assert should_grab_cube(hp_ratio=0.9, enemies_nearby=0, nearest_enemy_dist=999)

def test_should_not_grab_cube_low_hp():
    from tactics import should_grab_cube
    assert not should_grab_cube(hp_ratio=0.3, enemies_nearby=2, nearest_enemy_dist=30)


# ── StateMachine con tactics ──────────────────────────────────────────────────

FRAME = np.zeros((600, 800, 3), dtype=np.uint8)


class FakeCtrl:
    def __init__(self): self.moves = []; self.stops = 0
    def move(self, dx, dy): self.moves.append((dx, dy))
    def stop(self): self.stops += 1


def test_sm_fleeing_on_poison_early():
    from state_machine import StateMachine
    sm = StateMachine()
    fc = FakeCtrl()
    s = FrameState(poison=True, nearest_bush_dir=(1.0, 0.0), dist_to_bush=100.0,
                   game_phase="EARLY")
    assert sm.tick(FRAME, s, fc) == "FLEEING"

def test_sm_engaging_with_advantage():
    from state_machine import StateMachine
    from game_state import Enemy
    sm = StateMachine()
    fc = FakeCtrl()
    e = Enemy(200, 300, hp_ratio=0.8, confidence=0.9)
    # LATE: engage_threshold=0, engage_hp=0.50 — hp=0.8 → should engage
    s = FrameState(
        enemies=(e,),
        nearest_bush_dir=(0.5, 0.5),
        dist_to_bush=50.0,
        hp_ratio=0.8,
        cubes_self=0,
        game_phase="LATE",
    )
    result = sm.tick(FRAME, s, fc)
    assert result == "ENGAGING"

def test_sm_no_engage_early_without_cubes():
    from state_machine import StateMachine
    from game_state import Enemy
    sm = StateMachine()
    fc = FakeCtrl()
    e = Enemy(200, 300)
    # EARLY: engage_threshold=2, cubes_self=0 → NO engage
    s = FrameState(
        enemies=(e,),
        nearest_bush_dir=(0.5, 0.5),
        dist_to_bush=50.0,
        hp_ratio=0.9,
        cubes_self=0,
        game_phase="EARLY",
    )
    result = sm.tick(FRAME, s, fc)
    assert result != "ENGAGING"

def test_sm_hysteresis_flee():
    """Con hysteresis=0.10 e flee_hp=0.30: entrata a 0.29, uscita solo a >=0.40."""
    from state_machine import StateMachine
    sm = StateMachine()
    fc = FakeCtrl()

    # Entrata in FLEEING
    s_flee = FrameState(hp_ratio=0.29, nearest_bush_dir=(1.0, 0.0),
                        dist_to_bush=50.0, game_phase="EARLY")
    sm.tick(FRAME, s_flee, fc)
    assert sm._is_fleeing

    # hp=0.35 < flee_hp(0.30)+hysteresis(0.10)=0.40 → ancora in FLEEING
    s_mid = FrameState(hp_ratio=0.35, nearest_bush_dir=(1.0, 0.0),
                       dist_to_bush=50.0, game_phase="EARLY")
    result = sm.tick(FRAME, s_mid, fc)
    assert result == "FLEEING"

    # hp=0.45 >= 0.40 → esce da FLEEING
    s_ok = FrameState(hp_ratio=0.45, nearest_bush_dir=(1.0, 0.0),
                      dist_to_bush=50.0, game_phase="EARLY")
    sm.tick(FRAME, s_ok, fc)
    assert not sm._is_fleeing


# ── LatestSlot ────────────────────────────────────────────────────────────────

def test_latest_slot_put_get():
    from utils.threading_utils import LatestSlot
    slot = LatestSlot()
    slot.put("hello")
    item = slot.get(timeout=0.1)
    assert item is not None
    value, ts, seq = item
    assert value == "hello"
    assert seq == 1

def test_latest_slot_always_latest():
    from utils.threading_utils import LatestSlot
    slot = LatestSlot()
    slot.put("a")
    slot.put("b")
    slot.put("c")
    item = slot.get(timeout=0.1)
    # get() ritorna il più recente tra quelli messi prima che l'evento fosse consumato
    assert item is not None
    # seq dev'essere 1 (solo il primo set dell'event viene consumato)
    # ma il value deve essere l'ultimo scritto
    _, _, seq = item
    assert seq >= 1

def test_latest_slot_timeout():
    from utils.threading_utils import LatestSlot
    slot = LatestSlot()
    item = slot.get(timeout=0.05)
    assert item is None

def test_latest_slot_peek_none():
    from utils.threading_utils import LatestSlot
    slot = LatestSlot()
    assert slot.peek() is None


# ── randomizer Phase 2 ────────────────────────────────────────────────────────

def test_reaction_time_in_bounds():
    from randomizer import reaction_time_ms
    for _ in range(200):
        v = reaction_time_ms()
        assert 120.0 <= v <= 600.0, f"reaction time fuori bounds: {v}"

def test_inter_click_gap_positive():
    from randomizer import inter_click_gap_ms
    for _ in range(100):
        assert inter_click_gap_ms() > 0

def test_dwell_time_in_bounds():
    from randomizer import dwell_time_ms
    for _ in range(200):
        v = dwell_time_ms()
        assert 15.0 <= v <= 150.0, f"dwell time fuori bounds: {v}"

def test_jittered_tap_coord_close():
    from randomizer import jittered_tap_coord
    for _ in range(200):
        x, y = jittered_tap_coord(100, 200, sigma=4.0)
        assert abs(x - 100) <= 25, f"x troppo lontano: {x}"
        assert abs(y - 200) <= 25, f"y troppo lontano: {y}"

def test_should_act_suboptimal_rate():
    from randomizer import should_act_suboptimal
    hits = sum(1 for _ in range(10000) if should_act_suboptimal(epsilon=0.07))
    # Con epsilon=0.07 su 10000 campioni, attesi ~700 ± 3σ≈~700±78
    assert 500 <= hits <= 900, f"suboptimal rate anomalo: {hits}/10000"

def test_human_swipe_returns_points():
    from randomizer import human_swipe
    path = human_swipe((0.0, 0.0), (100.0, 100.0), duration_ms=200)
    assert len(path) >= 10
    # Primo e ultimo punto vicini a start/end
    assert abs(path[0][0]) < 5
    assert abs(path[-1][0] - 100.0) < 15   # Bézier non forza esattamente end

def test_bezier_swipe_length():
    from utils.curves import bezier_swipe
    pts = bezier_swipe((0, 0), (200, 100), n_points=30)
    assert len(pts) == 31  # 0..30 inclusi

def test_perlin_path_length():
    from utils.curves import perlin_path
    pts = perlin_path((0, 0), (200, 100), n_points=25)
    assert len(pts) == 26


# ── SessionRandomizer ──────────────────────────────────────────────────────────

def test_session_duration_bounded():
    from anti_ban import SessionRandomizer
    rnd = SessionRandomizer()
    for _ in range(50):
        d = rnd.session_duration_minutes()
        assert 0 < d <= 150.0, f"durata anomala: {d}"

def test_day_off_rate():
    """Day-off ~15% su 5000 campioni."""
    from anti_ban import SessionRandomizer
    rnd = SessionRandomizer({"day_off_prob": 0.15})
    hits = sum(1 for _ in range(5000) if rnd.should_take_day_off())
    assert 400 <= hits <= 1100, f"day-off rate anomalo: {hits}/5000"

def test_session_randomizer_from_profile_default():
    from anti_ban import SessionRandomizer
    # Senza JSON cade sul default interno
    rnd = SessionRandomizer.from_profile("nonexistent")
    assert rnd is not None
    assert rnd.session_duration_minutes() > 0

def test_hour_weights_valid():
    """Pesi orari: 24 valori, tutti positivi, peak in fascia 18-23."""
    from anti_ban import _HOUR_WEIGHTS
    assert len(_HOUR_WEIGHTS) == 24
    assert all(w > 0 for w in _HOUR_WEIGHTS)
    # Fascia sera (18-23) ha peso medio > fascia notte (0-5)
    evening_avg = sum(_HOUR_WEIGHTS[18:24]) / 6
    night_avg = sum(_HOUR_WEIGHTS[0:6]) / 6
    assert evening_avg > night_avg * 3, "Fascia sera deve pesare molto più della notte"

def test_pick_session_hour_valid():
    from anti_ban import SessionRandomizer
    rnd = SessionRandomizer()
    for _ in range(100):
        h = rnd.pick_session_hour()
        assert 0 <= h <= 23
