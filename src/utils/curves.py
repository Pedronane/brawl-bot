"""Curve di Bézier cubiche per swipe/movimento umano.

Invece di traiettorie lineari (rilevabili da anti-bot), genera percorsi
con punti di controllo casuali + micro-jitter stocastico.

Letteratura: Castle.io, IJIRT 2024 — curve troppo "perfette" rilevabili,
serve rumore Perlin-style o sub-movimenti.
"""
from __future__ import annotations

import math
import random


def _cubic_bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    """Punto su curva di Bézier cubica al parametro t ∈ [0, 1]."""
    mt = 1.0 - t
    x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
    y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
    return x, y


def bezier_swipe(
    start: tuple[float, float],
    end: tuple[float, float],
    n_points: int = 40,
    control_jitter: float = 25.0,
    point_jitter: float = 1.5,
) -> list[tuple[float, float]]:
    """Genera traiettoria Bézier cubica con rumore sui punti intermedi.

    Args:
        start: coordinate (x, y) di partenza
        end: coordinate (x, y) di arrivo
        n_points: numero di punti sulla curva (più = più smooth)
        control_jitter: deviazione massima dei punti di controllo (px)
        point_jitter: rumore gaussiano aggiunto a ogni punto finale (px)

    Returns:
        Lista di (x, y) punti lungo la traiettoria.
    """
    # Punti di controllo con offset casuale rispetto alla linea retta
    dx = end[0] - start[0]
    dy = end[1] - start[1]

    # cp1 vicino a start, cp2 vicino a end — offset perpendiculare random
    perp_x, perp_y = -dy, dx
    perp_len = math.hypot(perp_x, perp_y) + 1e-6
    perp_x /= perp_len
    perp_y /= perp_len

    off1 = random.gauss(0, control_jitter)
    off2 = random.gauss(0, control_jitter)

    cp1 = (
        start[0] + dx * 0.33 + perp_x * off1,
        start[1] + dy * 0.33 + perp_y * off1,
    )
    cp2 = (
        start[0] + dx * 0.67 + perp_x * off2,
        start[1] + dy * 0.67 + perp_y * off2,
    )

    points: list[tuple[float, float]] = []
    for i in range(n_points + 1):
        t = i / n_points
        x, y = _cubic_bezier(start, cp1, cp2, end, t)
        # Micro-jitter su ogni punto (sub-movimenti umani)
        if 0 < i < n_points and point_jitter > 0:
            x += random.gauss(0, point_jitter)
            y += random.gauss(0, point_jitter)
        points.append((x, y))

    return points


def perlin_path(
    start: tuple[float, float],
    end: tuple[float, float],
    n_points: int = 40,
    amplitude: float = 8.0,
) -> list[tuple[float, float]]:
    """Alternativa Perlin-style: sinusoide con frequenza/fase random lungo il percorso.

    Utile quando Bézier è troppo "pulito" per anti-cheat avanzati.
    """
    freq = random.uniform(1.5, 3.5)
    phase = random.uniform(0, math.tau)
    amp = random.uniform(amplitude * 0.5, amplitude * 1.5)

    # Direzione perpendicolare
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy) + 1e-6
    perp_x, perp_y = -dy / length, dx / length

    points = []
    for i in range(n_points + 1):
        t = i / n_points
        bx = start[0] + dx * t
        by = start[1] + dy * t
        wave = amp * math.sin(freq * math.pi * t + phase)
        points.append((bx + perp_x * wave, by + perp_y * wave))
    return points
