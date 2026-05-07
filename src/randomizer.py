"""Randomizzazione timing, input e traiettorie per anti-ban.

Principi:
  1. Reaction time gaussiano μ=250ms σ=80ms — non uniforme (rilevabile)
  2. Inter-click log-normale — code lunghe verso pause grandi (umano reale)
  3. Dwell time 40-120ms — mousedown→mouseup
  4. ε-suboptimal: 7% azioni deliberatamente sbagliate (bot troppo perfetto = flaggato)
  5. Noise posizionale gaussiano ±4px sui tap
  6. Bézier swipe via utils.curves (traiettorie non-lineari)

Backward compat: jittered_interval, keystroke_gap, maybe_human_pause, noisy_direction
restano con stessa firma.
"""
from __future__ import annotations

import math
import random
import time

import numpy as np

from config import (
    INPUT_DELAY_CHANCE,
    INPUT_DELAY_MAX,
    INPUT_DELAY_MIN,
    KEYSTROKE_INTERVAL_MAX,
    KEYSTROKE_INTERVAL_MIN,
    LOOP_INTERVAL,
    TIMING_JITTER_PCT,
)
from utils.curves import bezier_swipe, perlin_path

# ── Costanti distribuzione umana (fonti: paper Castle.io, IJIRT 2024) ─────────
_RT_MEAN_MS = 250.0      # reaction time media
_RT_STD_MS = 80.0        # deviazione standard
_RT_MIN_MS = 120.0       # cutoff basso
_RT_MAX_MS = 600.0       # cutoff alto
_DWELL_MEAN_MS = 70.0    # mousedown→mouseup media
_DWELL_STD_MS = 25.0
_DWELL_MIN_MS = 15.0
_DWELL_MAX_MS = 150.0
_EPSILON = 0.07           # probabilità azione subottimale
_TAP_SIGMA_PX = 4.0       # noise posizionale tap


# ── Backward-compat (invariati) ────────────────────────────────────────────────

def jittered_interval() -> float:
    """LOOP_INTERVAL ± TIMING_JITTER_PCT (uniform, backward compat)."""
    jitter = LOOP_INTERVAL * TIMING_JITTER_PCT
    return LOOP_INTERVAL + random.uniform(-jitter, jitter)


def keystroke_gap() -> float:
    """Ritardo realistico tra tasti consecutivi."""
    return random.uniform(KEYSTROKE_INTERVAL_MIN, KEYSTROKE_INTERVAL_MAX)


def maybe_human_pause() -> None:
    """15% chance: micro-pausa umana tra azioni."""
    if random.random() < INPUT_DELAY_CHANCE:
        time.sleep(random.uniform(INPUT_DELAY_MIN, INPUT_DELAY_MAX))


def noisy_direction(dx: float, dy: float, noise_deg: float = 8.0) -> tuple[float, float]:
    """Rumore angolare ±noise_deg sulla direzione. Backward compat."""
    angle = math.radians(random.uniform(-noise_deg, noise_deg))
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    nx = dx * cos_a - dy * sin_a
    ny = dx * sin_a + dy * cos_a
    mag = math.hypot(nx, ny)
    if mag < 1e-6:
        return dx, dy
    return nx / mag, ny / mag


# ── Nuove distribuzioni (anti-ban phase 2) ─────────────────────────────────────

def reaction_time_ms() -> float:
    """Reaction time gaussiano μ=250 σ=80 ms, clipped [120, 600].

    Usare come delay tra "vedo trigger" → "eseguo azione".
    """
    return float(np.clip(np.random.normal(_RT_MEAN_MS, _RT_STD_MS), _RT_MIN_MS, _RT_MAX_MS))


def inter_click_gap_ms() -> float:
    """Inter-click interval log-normale: code lunghe verso pause grandi (umano reale)."""
    # lognormal con μ_log=5.0 σ_log=0.7 → median≈148ms, mean≈200ms, code lunghe
    return float(np.clip(np.random.lognormal(5.0, 0.7), 80.0, 2000.0))


def dwell_time_ms() -> float:
    """Durata mousedown→mouseup gaussiana μ=70 σ=25 ms, clipped [15, 150]."""
    return float(np.clip(np.random.normal(_DWELL_MEAN_MS, _DWELL_STD_MS), _DWELL_MIN_MS, _DWELL_MAX_MS))


def should_act_suboptimal(epsilon: float = _EPSILON) -> bool:
    """True epsilon% del tempo — forza un'azione deliberatamente sbagliata.

    Bot che gioca troppo bene viene flaggato. 65° percentile umano = invisibile.
    """
    return random.random() < epsilon


def jittered_tap_coord(x: float, y: float, sigma: float = _TAP_SIGMA_PX) -> tuple[int, int]:
    """Coordinate tap con rumore gaussiano ±sigma px.

    Mai coordinate pixel-perfect: tap_coord += N(0, sigma).
    """
    nx = x + float(np.random.normal(0, sigma))
    ny = y + float(np.random.normal(0, sigma))
    return int(round(nx)), int(round(ny))


def reaction_sleep() -> None:
    """Dorme per un reaction time gaussiano realistico."""
    time.sleep(reaction_time_ms() / 1000.0)


# ── Swipe con traiettoria Bézier ───────────────────────────────────────────────

def human_swipe(
    start: tuple[float, float],
    end: tuple[float, float],
    duration_ms: float | None = None,
    use_perlin: bool = False,
) -> list[tuple[float, float]]:
    """Genera traiettoria swipe umanizzata (Bézier o Perlin-style).

    Args:
        start: (x, y) partenza in pixel
        end: (x, y) arrivo in pixel
        duration_ms: durata totale swipe (usa dwell_time se None)
        use_perlin: True → Perlin-style (più rumore, anti anti-cheat avanzati)

    Returns:
        Lista di punti (x, y) lungo la traiettoria.

    Esempio uso in controller.py::

        path = human_swipe(joystick_center, target)
        for pt in path:
            pyautogui.moveTo(*pt)
            time.sleep(step_delay)
    """
    n_points = max(20, int((duration_ms or dwell_time_ms()) / 4))
    if use_perlin:
        return perlin_path(start, end, n_points=n_points)
    return bezier_swipe(start, end, n_points=n_points)
