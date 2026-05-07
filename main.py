"""Bot Brawl Stars — entry point.

Architettura 3-thread:
  CaptureThread  → frame_slot → DetectThread → state_slot → Main (action loop)

Il thread principale gira a ~20 Hz (decisionale).
CaptureThread gira a ~30 FPS.
DetectThread gira alla velocità della detection CV (~20-40 FPS).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import controller as ctrl
from anti_ban import enforce_human_limits, log_session_stats
from behavior_engine import BehaviorEngine
from capture import WindowWatcher, capture, find_window
from config import WINDOW_TITLE, load_hsv_profile
from controller import reset_all_inputs, set_window_rect, stop
from detector import reset_match_timer
from game_modes.showdown import ShowdownMode
from logger import SessionLogger, log
from randomizer import jittered_interval
from state_machine import StateMachine
from utils.db_schema import open_db
from utils.image_proc import FrameSanity
from utils.resource_guard import ResourceGuard
from utils.threading_utils import CaptureThread, DetectThread, LatestSlot

_KILL_FLAG = Path(__file__).parent / "kill.flag"
_DB_PATH = Path(__file__).parent / "logs" / "brawl_bot.db"

# Profilo HSV da usare — cambia in "bluestacks_opengl" o "bluestacks_dx11" se serve
_HSV_PROFILE = "default"


def _kill_requested() -> bool:
    return _KILL_FLAG.exists()


def main() -> None:
    if _kill_requested():
        _KILL_FLAG.unlink()

    # ── Profilo HSV ───────────────────────────────────────────────────────────
    load_hsv_profile(_HSV_PROFILE)
    log.info(f"Profilo HSV: {_HSV_PROFILE}")

    # ── Trova finestra ────────────────────────────────────────────────────────
    log.info(f"Cerco finestra '{WINDOW_TITLE}'...")
    hwnd = find_window(WINDOW_TITLE)
    if not hwnd:
        log.error("BlueStacks non trovato. Aprilo e avvia Brawl Stars.")
        sys.exit(1)

    log.info("BlueStacks trovato. Avvio in 3 secondi.")
    log.info("Per fermare: Ctrl+C oppure crea il file 'kill.flag'.")
    time.sleep(3)

    # Warm-up capture per impostare rect iniziale
    frame_init, rect_init = capture(hwnd)
    set_window_rect(rect_init, hwnd)

    # ── Inizializza componenti ─────────────────────────────────────────────────
    conn = open_db(_DB_PATH)
    session_log = SessionLogger(conn)
    window_watch = WindowWatcher(WINDOW_TITLE)
    frame_sanity = FrameSanity(freeze_n=30, hash_diff_max=2)
    resource_guard = ResourceGuard(check_every=60)

    sm = StateMachine()
    mode = ShowdownMode()
    engine = BehaviorEngine(sm, mode, session_log)

    # Slot pipeline 3-thread
    frame_slot: LatestSlot = LatestSlot()
    state_slot: LatestSlot = LatestSlot()

    capture_t = CaptureThread(hwnd, frame_slot, window_watch, frame_sanity, target_fps=30)
    detect_t = DetectThread(frame_slot, state_slot, stale_ms=80)

    session_log.match_start()
    reset_match_timer()

    capture_t.start()
    detect_t.start()
    log.info("Pipeline 3-thread avviata.")

    frame_idx = 0

    try:
        while True:
            try:
                if _kill_requested():
                    log.info("kill.flag rilevato — bot fermato.")
                    _KILL_FLAG.unlink()
                    break

                enforce_human_limits()

                # Throttle se risorse alte
                if not resource_guard.tick():
                    time.sleep(0.05)
                    continue

                # Attendi nuovo state da DetectThread
                item = state_slot.get(timeout=0.3)
                if item is None:
                    continue

                (frame, state, rect), ts, seq = item
                set_window_rect(rect, hwnd)

                # Tick BehaviorEngine (include log transitions + DB sample)
                engine.update(frame, state, ctrl)

                frame_idx += 1
                if frame_idx % 300 == 0:
                    log_session_stats(frame_idx, sm.total_stuck)
                    log.debug(
                        f"[Pipeline] cap={capture_t.frames_captured} "
                        f"det={detect_t.frames_detected} "
                        f"stale={detect_t.frames_stale}"
                    )

                time.sleep(jittered_interval())

            except KeyboardInterrupt:
                log.info("Bot fermato (Ctrl+C).")
                break
            except Exception as exc:
                log.error(f"Errore frame {frame_idx}: {exc}")
                time.sleep(0.3)

    finally:
        log.info("Shutdown: fermo thread...")
        capture_t.stop()
        detect_t.stop()
        capture_t.join(timeout=2.0)
        detect_t.join(timeout=2.0)

        reset_all_inputs()
        stop()
        session_log.match_end(death_cause="unknown")
        conn.close()
        log.info(
            f"Bot terminato. "
            f"Frame: cap={capture_t.frames_captured} "
            f"det={detect_t.frames_detected} "
            f"stale={detect_t.frames_stale}"
        )


if __name__ == "__main__":
    main()
