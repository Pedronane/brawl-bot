from __future__ import annotations

import json
from pathlib import Path

import numpy as np

WINDOW_TITLE = "BlueStacks"

# Profilo HSV attivo — sovrascrivibile via load_hsv_profile()
HSV_PROFILE_NAME: str = "default"


def load_hsv_profile(profile_name: str = "default") -> None:
    """Carica profilo HSV da config/hsv_profiles.json e sovrascrive i valori globali.

    Chiamare PRIMA di avviare il bot se si usa un profilo non-default.
    Esempio: load_hsv_profile("bluestacks_opengl")
    """
    global HSV_PROFILE_NAME
    global BUSH_HSV_LOWER, BUSH_HSV_UPPER
    global POISON_HSV_LOWER, POISON_HSV_UPPER
    global ENEMY_HP_HSV_LOWER_A, ENEMY_HP_HSV_UPPER_A
    global ENEMY_HP_HSV_LOWER_B, ENEMY_HP_HSV_UPPER_B
    global AFK_HSV_LOWER, AFK_HSV_UPPER

    profiles_path = Path(__file__).parent.parent / "config" / "hsv_profiles.json"
    if not profiles_path.exists():
        return   # mantieni valori default hard-coded

    with profiles_path.open() as f:
        profiles = json.load(f)

    profile = profiles.get(profile_name) or profiles.get("default", {})
    HSV_PROFILE_NAME = profile_name

    def _arr(key: str, fallback) -> np.ndarray:
        return np.array(profile[key], dtype=np.uint8) if key in profile else fallback

    BUSH_HSV_LOWER = _arr("BUSH_HSV_LOWER", BUSH_HSV_LOWER)
    BUSH_HSV_UPPER = _arr("BUSH_HSV_UPPER", BUSH_HSV_UPPER)
    POISON_HSV_LOWER = _arr("POISON_HSV_LOWER", POISON_HSV_LOWER)
    POISON_HSV_UPPER = _arr("POISON_HSV_UPPER", POISON_HSV_UPPER)
    ENEMY_HP_HSV_LOWER_A = _arr("ENEMY_HP_HSV_LOWER_A", ENEMY_HP_HSV_LOWER_A)
    ENEMY_HP_HSV_UPPER_A = _arr("ENEMY_HP_HSV_UPPER_A", ENEMY_HP_HSV_UPPER_A)
    ENEMY_HP_HSV_LOWER_B = _arr("ENEMY_HP_HSV_LOWER_B", ENEMY_HP_HSV_LOWER_B)
    ENEMY_HP_HSV_UPPER_B = _arr("ENEMY_HP_HSV_UPPER_B", ENEMY_HP_HSV_UPPER_B)
    AFK_HSV_LOWER = _arr("AFK_HSV_LOWER", AFK_HSV_LOWER)
    AFK_HSV_UPPER = _arr("AFK_HSV_UPPER", AFK_HSV_UPPER)

# ── Controllo ──────────────────────────────────────────────────────────────────
# "keyboard" → WASD (configurare BlueStacks Game Controls → MOBA mode)
# "mouse"    → joystick virtuale via mouse drag (lato sinistro schermo)
CONTROL_MODE = "keyboard"

# Solo per CONTROL_MODE = "mouse"
JOYSTICK_X = 0.20
JOYSTICK_Y = 0.78
JOYSTICK_DRAG_RADIUS = 70

# ── Posizione player ───────────────────────────────────────────────────────────
PLAYER_CENTER_X = 0.5
PLAYER_CENTER_Y = 0.5

# ── Colori HSV ────────────────────────────────────────────────────────────────
BUSH_HSV_LOWER = np.array([87, 90, 25])
BUSH_HSV_UPPER = np.array([122, 255, 165])

POISON_HSV_LOWER = np.array([145, 100, 60])
POISON_HSV_UPPER = np.array([175, 255, 210])

ENEMY_HP_HSV_LOWER_A = np.array([0,  160, 120])
ENEMY_HP_HSV_UPPER_A = np.array([8,  255, 255])
ENEMY_HP_HSV_LOWER_B = np.array([172, 160, 120])
ENEMY_HP_HSV_UPPER_B = np.array([180, 255, 255])

AFK_HSV_LOWER = np.array([18, 140, 140])
AFK_HSV_UPPER = np.array([35, 255, 255])

# ── Soglie ─────────────────────────────────────────────────────────────────────
BUSH_MIN_AREA = 800
BUSH_MORPH_KERNEL = 7

UI_EXCLUDE = [
    (0.0, 0.68, 0.28, 1.0),
    (0.72, 0.60, 1.0,  1.0),
    (0.88, 0.0,  1.0,  0.85),
    (0.0,  0.0,  1.0,  0.06),
]
BUSH_REACH_DIST = 8
POISON_EDGE_FRACTION = 0.18
POISON_PIXEL_RATIO = 0.18
AFK_ROI_PIXEL_SUM = 2500

WIGGLE_INTERVAL = 35
WIGGLE_DURATION = 0.09

LOOP_INTERVAL = 0.08

# ── Anti-ban randomization ─────────────────────────────────────────────────────
TIMING_JITTER_PCT = 0.20          # ±20% su LOOP_INTERVAL
INPUT_DELAY_CHANCE = 0.15         # 15% probabilità di delay extra umano
INPUT_DELAY_MIN = 0.08            # secondi delay umano min
INPUT_DELAY_MAX = 0.28            # secondi delay umano max
KEYSTROKE_INTERVAL_MIN = 0.005   # secondi tra keyDown/keyUp staggered
KEYSTROKE_INTERVAL_MAX = 0.015

# ── Anti-ban limiti sessione ───────────────────────────────────────────────────
SESSION_MAX_MINUTES = 45          # pausa forzata dopo N minuti attivi
SESSION_BREAK_MINUTES = 5         # durata pausa forzata

# ── State machine / wall avoidance ────────────────────────────────────────────
STUCK_FRAMES  = 4    # frame consecutivi immobili → stuck
STUCK_DIFF    = 6.0  # diff pixel media sotto questa = immobile
COMMIT_FRAMES = 14   # frame da mantenere la direzione deviata
BACKUP_FRAMES = 5    # frame iniziali di backup (direzione opposta)
AVOID_ANGLE   = 70   # gradi di deviazione dalla direzione originale
