"""
debug.py — visualizza cosa vede il bot in tempo reale.

Tasti:
  q → esci
  h → mostra solo maschera bush (per calibrare BUSH_HSV_*)
  p → mostra solo maschera veleno
  e → mostra solo maschera nemici
  n → vista normale con overlay
"""

import sys
import cv2
import numpy as np
from capture import find_window, capture
from detector import (
    detect_bushes, detect_enemies, detect_poison,
    detect_afk_warning, is_in_bush, _hsv,
)
from config import (
    WINDOW_TITLE, PLAYER_CENTER_X, PLAYER_CENTER_Y,
    BUSH_HSV_LOWER, BUSH_HSV_UPPER,
    POISON_HSV_LOWER, POISON_HSV_UPPER,
    ENEMY_HP_HSV_LOWER_A, ENEMY_HP_HSV_UPPER_A,
    ENEMY_HP_HSV_LOWER_B, ENEMY_HP_HSV_UPPER_B,
)


def main() -> None:
    hwnd = find_window(WINDOW_TITLE)
    if not hwnd:
        print("BlueStacks non trovato.")
        sys.exit(1)

    mode = "n"

    while True:
        frame, _ = capture(hwnd)
        h, w = frame.shape[:2]
        px, py = int(w * PLAYER_CENTER_X), int(h * PLAYER_CENTER_Y)

        if mode == "h":
            mask = cv2.inRange(_hsv(frame), BUSH_HSV_LOWER, BUSH_HSV_UPPER)
            out = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            cv2.putText(out, "BUSH MASK (h=normal)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        elif mode == "p":
            mask = cv2.inRange(_hsv(frame), POISON_HSV_LOWER, POISON_HSV_UPPER)
            out = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            cv2.putText(out, "POISON MASK (p=normal)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

        elif mode == "e":
            m1 = cv2.inRange(_hsv(frame), ENEMY_HP_HSV_LOWER_A, ENEMY_HP_HSV_UPPER_A)
            m2 = cv2.inRange(_hsv(frame), ENEMY_HP_HSV_LOWER_B, ENEMY_HP_HSV_UPPER_B)
            out = cv2.cvtColor(m1 | m2, cv2.COLOR_GRAY2BGR)
            cv2.putText(out, "ENEMY HP MASK (e=normal)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        else:
            out = frame.copy()
            bushes  = detect_bushes(frame)
            enemies = detect_enemies(frame)
            poison  = detect_poison(frame)
            afk     = detect_afk_warning(frame)
            hidden  = is_in_bush(frame)

            for bx, by, area in bushes:
                cv2.circle(out, (bx, by), 12, (0, 255, 0), 2)
                cv2.putText(out, f"{int(area)}", (bx + 14, by),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 0), 1)

            for ex, ey in enemies:
                cv2.circle(out, (ex, ey), 15, (0, 0, 255), 2)

            cv2.circle(out, (px, py), 20, (255, 255, 255), 2)

            labels = [
                (f"Cespugli: {len(bushes)}", (0, 255, 0)),
                (f"Nemici visibili: {len(enemies)}", (0, 0, 255)),
                (f"Veleno: {poison}", (255, 0, 255)),
                (f"AFK warning: {afk}", (0, 255, 255)),
                (f"Nel cespuglio: {hidden}", (255, 255, 0)),
            ]
            for i, (text, color) in enumerate(labels):
                cv2.putText(out, text, (10, 30 + i * 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

            cv2.putText(out, "h=bush p=poison e=enemy q=quit", (10, h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        out_small = cv2.resize(out, (out.shape[1] // 2, out.shape[0] // 2))
        cv2.imshow("Brawl Bot Debug", out_small)

        key = cv2.waitKey(80) & 0xFF
        if key == ord("q"):
            break
        elif key in (ord("h"), ord("p"), ord("e"), ord("n")):
            mode = chr(key)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
