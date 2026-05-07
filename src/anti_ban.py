import time

from config import SESSION_BREAK_MINUTES, SESSION_MAX_MINUTES
from logger import log

_session_start = time.time()
_last_break    = time.time()


def enforce_human_limits() -> None:
    """Pausa forzata dopo SESSION_MAX_MINUTES di attività continua."""
    global _last_break
    elapsed = (time.time() - _last_break) / 60.0
    if elapsed >= SESSION_MAX_MINUTES:
        log.warning(f"Anti-ban: {SESSION_MAX_MINUTES}min attivi → pausa {SESSION_BREAK_MINUTES}min")
        time.sleep(SESSION_BREAK_MINUTES * 60)
        _last_break = time.time()
        log.info("Anti-ban: pausa terminata, ripresa.")


def session_elapsed_minutes() -> float:
    return (time.time() - _session_start) / 60.0


def log_session_stats(frame_idx: int, stuck_count: int) -> None:
    elapsed = session_elapsed_minutes()
    stuck_ratio = stuck_count / max(frame_idx, 1)
    log.debug(f"Stats | frame={frame_idx} elapsed={elapsed:.1f}min stuck_ratio={stuck_ratio:.3f}")
    if stuck_ratio > 0.10:
        log.warning(f"Stuck ratio alto ({stuck_ratio:.1%}) — calibra AVOID_ANGLE o HSV")
