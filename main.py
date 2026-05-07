import os
import sys
import time
from pathlib import Path

# Aggiungi src/ al path così gli import nei moduli restano semplici
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import controller as ctrl
from anti_ban import enforce_human_limits, log_session_stats
from capture import capture, find_window
from config import WINDOW_TITLE
from controller import reset_all_inputs, set_window_rect, stop
from detector import detect_afk_warning, detect_poison, is_in_bush, nearest_bush_direction
from game_state import FrameState
from logger import log
from randomizer import jittered_interval
from state_machine import StateMachine

_KILL_FLAG = Path(__file__).parent / "kill.flag"


def _kill_requested() -> bool:
    """Crea il file 'kill.flag' nella cartella del bot per fermarlo."""
    return _KILL_FLAG.exists()


def main() -> None:
    if _kill_requested():
        _KILL_FLAG.unlink()

    log.info(f"Cerco finestra '{WINDOW_TITLE}'...")
    hwnd = find_window(WINDOW_TITLE)
    if not hwnd:
        log.error("BlueStacks non trovato. Aprilo e avvia Brawl Stars.")
        sys.exit(1)

    log.info("BlueStacks trovato. Avvio in 3 secondi.")
    log.info("Per fermare: Ctrl+C oppure crea il file 'kill.flag' nella cartella bot.")
    time.sleep(3)

    frame, rect = capture(hwnd)
    set_window_rect(rect, hwnd)

    sm = StateMachine()
    frame_idx = 0

    try:
        while True:
            try:
                if _kill_requested():
                    log.info("kill.flag rilevato — bot fermato.")
                    _KILL_FLAG.unlink()
                    break

                enforce_human_limits()

                frame, rect = capture(hwnd)
                set_window_rect(rect, hwnd)

                direction, dist = nearest_bush_direction(frame)
                state = FrameState(
                    poison=detect_poison(frame),
                    afk=detect_afk_warning(frame),
                    in_bush=is_in_bush(frame),
                    nearest_bush_dir=direction,
                    dist_to_bush=dist,
                    frame_idx=frame_idx,
                )

                current_state = sm.tick(frame, state, ctrl)

                if current_state != sm.prev_state:
                    reasons = []
                    if state.poison:
                        reasons.append("veleno")
                    if state.afk:
                        reasons.append("AFK warning")
                    if state.in_bush:
                        reasons.append("in cespuglio")
                    if sm.commit_left > 0:
                        reasons.append("avoid muro")
                    log.info(
                        f"[{current_state:7s}] "
                        f"{', '.join(reasons) if reasons else f'dist={dist:.0f}'}"
                    )
                    sm.prev_state = current_state

                frame_idx += 1
                if frame_idx % 300 == 0:
                    log_session_stats(frame_idx, sm.total_stuck)

                time.sleep(jittered_interval())

            except KeyboardInterrupt:
                log.info("Bot fermato (Ctrl+C).")
                break
            except Exception as exc:
                log.error(f"Errore frame {frame_idx}: {exc}")
                time.sleep(0.3)

    finally:
        # Garantito: rilascia SEMPRE tasti e mouse, anche su crash/kill
        reset_all_inputs()
        stop()
        log.info("Input rilasciati. Bot terminato.")


if __name__ == "__main__":
    main()
