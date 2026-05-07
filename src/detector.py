from __future__ import annotations

import time

import cv2
import numpy as np

from config import (
    AFK_HSV_LOWER,
    AFK_HSV_UPPER,
    AFK_ROI_PIXEL_SUM,
    BUSH_HSV_LOWER,
    BUSH_HSV_UPPER,
    BUSH_MIN_AREA,
    BUSH_MORPH_KERNEL,
    ENEMY_HP_HSV_LOWER_A,
    ENEMY_HP_HSV_LOWER_B,
    ENEMY_HP_HSV_UPPER_A,
    ENEMY_HP_HSV_UPPER_B,
    PLAYER_CENTER_X,
    PLAYER_CENTER_Y,
    POISON_EDGE_FRACTION,
    POISON_HSV_LOWER,
    POISON_HSV_UPPER,
    POISON_PIXEL_RATIO,
    UI_EXCLUDE,
)
from game_state import Enemy
from utils.image_proc import TemporalFilter

_MORPH3 = np.ones((3, 3), np.uint8)
_MORPH5 = np.ones((5, 5), np.uint8)

# TemporalFilter condiviso per enemies — istanza modulo (un solo thread detect).
_enemy_filter = TemporalFilter(window=3, radius=40, threshold=2)

# Tempo inizio partita per stima game_phase da timer
_match_start_ts: float = time.monotonic()


def detect_all(frame: np.ndarray, frame_idx: int = 0):
    """Entry-point unico per DetectThread: esegui tutte le detection → FrameState.

    Importa FrameState lazy per evitare import circolari.
    """
    from game_state import FrameState

    direction, dist = nearest_bush_direction(frame)
    enemies = detect_enemies(frame)
    poison = detect_poison(frame)
    afk = detect_afk_warning(frame)
    in_bush = is_in_bush(frame)
    phase = detect_game_phase(players_left=0, poison_progress=0.0)

    return FrameState(
        poison=poison,
        afk=afk,
        in_bush=in_bush,
        nearest_bush_dir=direction,
        dist_to_bush=dist,
        frame_idx=frame_idx,
        enemies=tuple(enemies),
        game_phase=phase,
    )


def reset_match_timer() -> None:
    """Chiama all'inizio di ogni partita per azzerare il timer di game_phase."""
    global _match_start_ts
    _match_start_ts = time.monotonic()
    _enemy_filter.reset()


def _mask_ui(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape[:2]
    for x1f, y1f, x2f, y2f in UI_EXCLUDE:
        x1, y1 = int(w * x1f), int(h * y1f)
        x2, y2 = int(w * x2f), int(h * y2f)
        mask[y1:y2, x1:x2] = 0
    return mask


def _hsv(frame: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)


def _right_angle_ratio(cnt) -> float:
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)
    pts = approx.reshape(-1, 2).astype(float)
    n = len(pts)
    if n < 3:
        return 0.0
    right = 0
    for i in range(n):
        a = pts[(i - 1) % n]
        b = pts[i]
        c = pts[(i + 1) % n]
        ba = a - b
        bc = c - b
        denom = np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6
        cos_a = np.dot(ba, bc) / denom
        if abs(cos_a) < 0.4:
            right += 1
    return right / n


# ── Bush detection ─────────────────────────────────────────────────────────────

def _bush_contours(frame: np.ndarray):
    k = np.ones((BUSH_MORPH_KERNEL, BUSH_MORPH_KERNEL), np.uint8)
    mask = cv2.inRange(_hsv(frame), BUSH_HSV_LOWER, BUSH_HSV_UPPER)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _MORPH3)
    mask = _mask_ui(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    result = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < BUSH_MIN_AREA:
            continue
        if _right_angle_ratio(c) > 0.45:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.03 * peri, True)
        if len(approx) <= 4 and area > 12000:
            continue
        result.append(c)
    return result


def detect_bushes(frame: np.ndarray) -> list[tuple[int, int, float]]:
    result = []
    for cnt in _bush_contours(frame):
        area = cv2.contourArea(cnt)
        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        result.append((cx, cy, area))
    return result


def nearest_bush_direction(frame: np.ndarray) -> tuple[tuple[float, float] | None, float]:
    h, w = frame.shape[:2]
    px, py = int(w * PLAYER_CENTER_X), int(h * PLAYER_CENTER_Y)
    player = np.array([px, py], dtype=np.float32)

    contours = _bush_contours(frame)
    if not contours:
        return None, float("inf")

    best_dist = float("inf")
    best_dx, best_dy = 0.0, 0.0

    for cnt in contours:
        pts = cnt.reshape(-1, 2).astype(np.float32)
        dists = np.linalg.norm(pts - player, axis=1)
        idx = int(np.argmin(dists))
        d = float(dists[idx])
        if d < best_dist:
            best_dist = d
            best_dx = float(pts[idx][0]) - px
            best_dy = float(pts[idx][1]) - py

    if best_dist < 1.0:
        return (0.0, 0.0), 0.0
    return (best_dx / best_dist, best_dy / best_dist), best_dist


# ── Enemy detection (HP-bar anchor + TemporalFilter) ──────────────────────────

def detect_enemies(frame: np.ndarray) -> list[Enemy]:
    """Rileva nemici via HP-bar rossa. Output filtrato da TemporalFilter N=3."""
    hsv = _hsv(frame)
    mask = cv2.inRange(hsv, ENEMY_HP_HSV_LOWER_A, ENEMY_HP_HSV_UPPER_A)
    mask |= cv2.inRange(hsv, ENEMY_HP_HSV_LOWER_B, ENEMY_HP_HSV_UPPER_B)

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3)))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    raw: list[Enemy] = []
    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        # HP-bar: rettangolo orizzontale, aspect ratio cw/ch > 3
        if cw < 18 or ch >= 14 or cw <= ch * 3:
            continue
        # HP ratio stima: larghezza barra rossa / larghezza totale attesa
        hp_r = min(1.0, cw / 60.0)
        # Posizione nemico: centro barra + offset verso il basso
        ex = x + cw // 2
        ey = y + ch + 45          # sprite nemico ~45px sotto la barra
        raw.append(Enemy(ex, ey, hp_ratio=hp_r, confidence=0.8))

    confirmed = _enemy_filter.update(raw)
    return [Enemy(*c) if not isinstance(c, Enemy) else c for c in confirmed]


# ── Poison / AFK ──────────────────────────────────────────────────────────────

def detect_poison(frame: np.ndarray) -> bool:
    h, w = frame.shape[:2]
    mask = cv2.inRange(_hsv(frame), POISON_HSV_LOWER, POISON_HSV_UPPER)
    mask = _mask_ui(mask)

    m = int(min(h, w) * POISON_EDGE_FRACTION)
    strips = [
        mask[:m, m:w - m],
        mask[h - m:, m:w - m],
        mask[m:h - m, :m],
        mask[m:h - m, w - m:],
    ]
    for strip in strips:
        total = strip.size
        if total == 0:
            continue
        if np.count_nonzero(strip) / total > POISON_PIXEL_RATIO:
            return True
    return False


def detect_afk_warning(frame: np.ndarray) -> bool:
    h, w = frame.shape[:2]
    roi = frame[int(h * 0.08):int(h * 0.38), int(w * 0.28):int(w * 0.72)]
    mask = cv2.inRange(_hsv(roi), AFK_HSV_LOWER, AFK_HSV_UPPER)
    return int(np.sum(mask)) > AFK_ROI_PIXEL_SUM * 255


def is_in_bush(frame: np.ndarray) -> bool:
    h, w = frame.shape[:2]
    px, py = int(w * PLAYER_CENTER_X), int(h * PLAYER_CENTER_Y)
    inner_r, outer_r = 22, 65

    y1, y2 = max(0, py - outer_r), min(h, py + outer_r)
    x1, x2 = max(0, px - outer_r), min(w, px + outer_r)
    roi = frame[y1:y2, x1:x2]
    if roi.size == 0:
        return False

    cy_r, cx_r = py - y1, px - x1
    Y, X = np.ogrid[:roi.shape[0], :roi.shape[1]]
    dist2 = (X - cx_r) ** 2 + (Y - cy_r) ** 2
    annulus = (dist2 >= inner_r ** 2) & (dist2 <= outer_r ** 2)

    bush_mask = cv2.inRange(_hsv(roi), BUSH_HSV_LOWER, BUSH_HSV_UPPER)
    annulus_px = int(annulus.sum())
    bush_px = int(np.count_nonzero(bush_mask[annulus]))
    if annulus_px == 0:
        return False
    return (bush_px / annulus_px) > 0.28


# ── Game phase detection ───────────────────────────────────────────────────────

def detect_game_phase(
    players_left: int = 0,
    poison_progress: float = 0.0,
    elapsed_sec: float | None = None,
) -> str:
    """Stima game phase da players_left, poison_progress o tempo trascorso.

    Priorità: players_left > poison_progress > timer.
    Fallback a timer se entrambi non disponibili (players_left == 0).
    """
    t = elapsed_sec if elapsed_sec is not None else (time.monotonic() - _match_start_ts)

    # Via players_left (più accurato quando disponibile)
    if players_left > 0:
        if players_left >= 7:
            return "EARLY"
        if 3 <= players_left < 7:
            return "MID"
        return "LATE"

    # Via poison_progress
    if poison_progress > 0.0:
        if poison_progress < 0.35:
            return "EARLY"
        if poison_progress < 0.70:
            return "MID"
        return "LATE"

    # Fallback timer (deterministico, bassa accuratezza)
    if t < 50:
        return "EARLY"
    if t < 100:
        return "MID"
    return "LATE"
