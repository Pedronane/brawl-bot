import sys
import time
import math
import numpy as np
from capture import find_window, capture
from detector import nearest_bush_direction, detect_poison, detect_afk_warning, is_in_bush
from controller import set_window_rect, move, stop
from config import WINDOW_TITLE, LOOP_INTERVAL, BUSH_REACH_DIST, WIGGLE_INTERVAL, WIGGLE_DURATION

STUCK_FRAMES    = 4    # frame consecutivi immobili → stuck
STUCK_DIFF      = 6.0  # diff pixel media sotto questa = immobile
COMMIT_FRAMES   = 14   # frame da mantenere la direzione deviata
BACKUP_FRAMES   = 5    # frame iniziali di backup (direzione opposta)
AVOID_ANGLE     = 70   # gradi di deviazione dalla direzione originale


def _center_roi(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    m = 38
    return frame[h // 2 - m:h // 2 + m, w // 2 - m:w // 2 + m].copy()


def _rotate(dx: float, dy: float, deg: float) -> tuple[float, float]:
    r = math.radians(deg)
    return (dx * math.cos(r) - dy * math.sin(r),
            dx * math.sin(r) + dy * math.cos(r))


def _log(state: str, reason: str) -> None:
    print(f"[{state:7s}] {reason}")


def main() -> None:
    print(f"Cerco finestra '{WINDOW_TITLE}'...")
    hwnd = find_window(WINDOW_TITLE)
    if not hwnd:
        print("BlueStacks non trovato. Aprilo e avvia Brawl Stars.")
        sys.exit(1)

    print("BlueStacks trovato. Avvio in 3 secondi — porta il focus su BlueStacks.")
    time.sleep(3)

    frame, rect = capture(hwnd)
    set_window_rect(rect)

    prev_state     = ""
    wiggle_counter = 0
    wiggle_step    = 0
    _WIGGLE_DIRS   = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    prev_roi       = None
    stuck_count    = 0
    deflect_sign   = 1      # alterna +angolo / -angolo dopo ogni avoidance
    commit_left    = 0      # frame rimasti di committed direction
    commit_dir     = None   # direzione committed
    avoid_phase    = 0      # 0=backup, 1=deviato

    while True:
        try:
            frame, rect = capture(hwnd)
            set_window_rect(rect)

            poison    = detect_poison(frame)
            afk       = detect_afk_warning(frame)
            in_bush   = is_in_bush(frame)
            direction, dist = nearest_bush_direction(frame)

            # ── Stuck detection (disabilitata durante poison/afk) ─────────────
            roi = _center_roi(frame)
            flee_active = poison or afk
            if prev_roi is not None and prev_roi.shape == roi.shape and not flee_active:
                diff = np.mean(np.abs(roi.astype(float) - prev_roi.astype(float)))
                is_moving_state = not (in_bush and not poison and not afk)
                if is_moving_state and commit_left == 0 and diff < STUCK_DIFF:
                    stuck_count += 1
                else:
                    stuck_count = 0
            elif flee_active:
                stuck_count = 0
                commit_left = 0   # annulla avoidance attivo se sta fuggendo
            prev_roi = roi

            # ── Wall avoidance: inizia committed sequence quando stuck ──────────
            if stuck_count >= STUCK_FRAMES and commit_left == 0 and direction:
                commit_left  = BACKUP_FRAMES + COMMIT_FRAMES
                avoid_phase  = 0
                stuck_count  = 0
                _orig_dir    = direction
                _backup_dir  = (-direction[0], -direction[1])
                _deviated    = _rotate(*direction, AVOID_ANGLE * deflect_sign)
                deflect_sign *= -1   # prossima volta dall'altro lato

            # ── Calcola direzione effettiva ────────────────────────────────────
            if commit_left > 0:
                commit_left -= 1
                if avoid_phase == 0 and commit_left <= COMMIT_FRAMES:
                    avoid_phase = 1         # finita fase backup, inizia deviazione
                effective_dir = _backup_dir if avoid_phase == 0 else _deviated
            else:
                effective_dir = direction

            # ── Macchina a stati ──────────────────────────────────────────────
            if (poison or afk) and effective_dir:
                # Flee: muovi sempre a piena velocità, ignora dist e in_bush
                state = "FLEEING"
                move(*effective_dir)
                wiggle_counter = 0

            elif in_bush and not poison and not afk:
                state = "HIDING"
                wiggle_counter += 1
                if wiggle_counter >= WIGGLE_INTERVAL:
                    d = _WIGGLE_DIRS[wiggle_step % len(_WIGGLE_DIRS)]
                    move(*d)
                    time.sleep(WIGGLE_DURATION)
                    stop()
                    wiggle_step    += 1
                    wiggle_counter  = 0
                else:
                    stop()

            elif effective_dir and dist > BUSH_REACH_DIST:
                state = "MOVING"
                move(*effective_dir)

            elif effective_dir:
                state = "HIDING"
                stop()

            else:
                state = "WAITING"
                stop()

            if state != prev_state:
                reasons = []
                if poison:              reasons.append("veleno")
                if afk:                 reasons.append("AFK warning")
                if in_bush:             reasons.append("in cespuglio")
                if commit_left > 0:     reasons.append("avoid muro")
                _log(state, ", ".join(reasons) if reasons else f"dist={dist:.0f}")
                prev_state = state

            time.sleep(LOOP_INTERVAL)

        except KeyboardInterrupt:
            print("\nBot fermato.")
            stop()
            break
        except Exception as exc:
            print(f"Errore: {exc}")
            stop()
            time.sleep(0.3)


if __name__ == "__main__":
    main()
