import random
import time

from config import (
    INPUT_DELAY_CHANCE,
    INPUT_DELAY_MAX,
    INPUT_DELAY_MIN,
    KEYSTROKE_INTERVAL_MAX,
    KEYSTROKE_INTERVAL_MIN,
    LOOP_INTERVAL,
    TIMING_JITTER_PCT,
)


def jittered_interval() -> float:
    """LOOP_INTERVAL ± TIMING_JITTER_PCT."""
    jitter = LOOP_INTERVAL * TIMING_JITTER_PCT
    return LOOP_INTERVAL + random.uniform(-jitter, jitter)


def keystroke_gap() -> float:
    """Ritardo realistico tra operazioni su tasti consecutivi."""
    return random.uniform(KEYSTROKE_INTERVAL_MIN, KEYSTROKE_INTERVAL_MAX)


def maybe_human_pause() -> None:
    """15% chance: inserisci micro-pausa come farebbe un umano."""
    if random.random() < INPUT_DELAY_CHANCE:
        time.sleep(random.uniform(INPUT_DELAY_MIN, INPUT_DELAY_MAX))


def noisy_direction(dx: float, dy: float, noise_deg: float = 8.0) -> tuple[float, float]:
    """Aggiunge rumore angolare a una direzione per sembrare meno meccanico."""
    import math
    angle = math.radians(random.uniform(-noise_deg, noise_deg))
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    nx = dx * cos_a - dy * sin_a
    ny = dx * sin_a + dy * cos_a
    mag = math.hypot(nx, ny)
    if mag < 1e-6:
        return dx, dy
    return nx / mag, ny / mag
