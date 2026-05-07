"""Anti-ban: limiti sessione, randomizzazione temporale, variazione comportamentale.

Livelli di protezione:
  1. Pausa forzata ogni SESSION_MAX_MINUTES (mantenuto per compat)
  2. SessionRandomizer: durata log-normale, bias orario, days-off randomizzati
  3. ε-suboptimal integrato in randomizer.py

Riferimenti: Irdeto anti-cheat industry, forum botting community (Metin2, OSRS).
"""
from __future__ import annotations

import json
import random
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from config import SESSION_BREAK_MINUTES, SESSION_MAX_MINUTES
from logger import log

_session_start = time.time()
_last_break = time.time()


# ── Backward-compat (invariato) ────────────────────────────────────────────────

def enforce_human_limits() -> None:
    """Pausa forzata dopo SESSION_MAX_MINUTES di attività continua."""
    global _last_break
    elapsed = (time.time() - _last_break) / 60.0
    if elapsed >= SESSION_MAX_MINUTES:
        log.warning(
            f"Anti-ban: {SESSION_MAX_MINUTES}min attivi → pausa {SESSION_BREAK_MINUTES}min"
        )
        time.sleep(SESSION_BREAK_MINUTES * 60)
        _last_break = time.time()
        log.info("Anti-ban: pausa terminata, ripresa.")


def session_elapsed_minutes() -> float:
    return (time.time() - _session_start) / 60.0


def log_session_stats(frame_idx: int, stuck_count: int) -> None:
    elapsed = session_elapsed_minutes()
    stuck_ratio = stuck_count / max(frame_idx, 1)
    log.debug(
        f"Stats | frame={frame_idx} elapsed={elapsed:.1f}min "
        f"stuck_ratio={stuck_ratio:.3f}"
    )
    if stuck_ratio > 0.10:
        log.warning(f"Stuck ratio alto ({stuck_ratio:.1%}) — calibra AVOID_ANGLE o HSV")


# ── SessionRandomizer ──────────────────────────────────────────────────────────

# Pesi orari: 18:00–23:00 = peak (70%), altri = rari (30%)
# Indice = ora del giorno [0..23]
_HOUR_WEIGHTS = [
    0.005, 0.003, 0.002, 0.002, 0.003, 0.005,  # 00-05: notte
    0.008, 0.012, 0.015, 0.018, 0.020, 0.022,  # 06-11: mattina
    0.025, 0.028, 0.030, 0.032, 0.035, 0.038,  # 12-17: pomeriggio
    0.055, 0.065, 0.070, 0.075, 0.065, 0.050,  # 18-23: sera (peak)
]
assert len(_HOUR_WEIGHTS) == 24


class SessionRandomizer:
    """Decide quando giocare e per quanto tempo.

    Usare all'avvio per decidere se saltare la sessione (day off) e
    per impostare la durata massima con distribuzione log-normale umana.

    Esempio::

        rnd = SessionRandomizer.from_profile("casual")
        if rnd.should_take_day_off():
            sys.exit(0)
        duration = rnd.session_duration_minutes()
        # usa duration come limite in main loop
    """

    _DEFAULT_PROFILE = {
        "day_off_prob": 0.15,
        "duration_mean_min": 45.0,
        "duration_std_min": 20.0,
        "duration_max_min": 150.0,
        "break_interval_min": 45.0,
        "break_duration_min": 5.0,
        "inter_match_delay_min": 0.05,   # minuti tra match
        "inter_match_delay_max": 0.50,
    }

    def __init__(self, profile: dict | None = None) -> None:
        self._p = {**self._DEFAULT_PROFILE, **(profile or {})}
        self._session_start = time.time()

    @classmethod
    def from_profile(cls, name: str = "default") -> "SessionRandomizer":
        """Carica profilo da config/anti_ban_profiles.json."""
        path = Path(__file__).parent.parent / "config" / "anti_ban_profiles.json"
        if path.exists():
            with path.open() as f:
                profiles = json.load(f)
            profile = profiles.get(name) or profiles.get("default")
            return cls(profile)
        return cls()

    def should_take_day_off(self) -> bool:
        """~15% chance di saltare la sessione (days off casuali)."""
        result = random.random() < self._p["day_off_prob"]
        if result:
            log.info("Anti-ban: day off — sessione saltata")
        return result

    def session_duration_minutes(self) -> float:
        """Durata sessione da distribuzione log-normale μ=45min σ=20min, max 2.5h."""
        mean = self._p["duration_mean_min"]
        std = self._p["duration_std_min"]
        max_min = self._p["duration_max_min"]
        # log-normale: exp(normal(log(mean), std/mean)) approssimazione
        sigma_log = std / mean
        mu_log = np.log(mean) - 0.5 * sigma_log ** 2
        duration = float(np.random.lognormal(mu_log, sigma_log))
        return min(duration, max_min)

    def pick_session_hour(self) -> int:
        """Sceglie ora del giorno con bias verso 18:00–23:00."""
        return random.choices(range(24), weights=_HOUR_WEIGHTS, k=1)[0]

    def should_play_now(self) -> bool:
        """True se l'ora corrente è coerente con il profilo di gioco umano."""
        current_hour = datetime.now().hour
        weight = _HOUR_WEIGHTS[current_hour]
        # Normalizza: peso massimo è ~0.075, normalizza a [0, 1] e soglia 0.30
        norm = weight / max(_HOUR_WEIGHTS)
        return norm >= 0.30 or random.random() < norm

    def inter_match_delay_s(self) -> float:
        """Pausa casuale tra un match e il successivo [min, max] in secondi."""
        lo = self._p["inter_match_delay_min"] * 60
        hi = self._p["inter_match_delay_max"] * 60
        return random.uniform(lo, hi)

    def session_expired(self) -> bool:
        """True se la sessione ha superato la durata decisa."""
        elapsed_min = (time.time() - self._session_start) / 60.0
        return elapsed_min >= self.session_duration_minutes()
