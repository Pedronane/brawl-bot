"""Monitor risorse CPU/RAM e throttle del loop principale."""
from __future__ import annotations

import gc
import logging

import psutil

log = logging.getLogger(__name__)

_proc = psutil.Process()

_RSS_MAX_BYTES = 1_500 * 1024 * 1024   # 1.5 GB
_CPU_MAX_PCT = 85.0
_CPU_WARN_STREAK = 10                   # frame consecutivi sopra soglia → throttle


class ResourceGuard:
    """Controlla RSS e CPU ogni check_every frame. Forza gc se necessario."""

    def __init__(
        self,
        check_every: int = 60,
        rss_max_mb: int = 1500,
        cpu_max_pct: float = 85.0,
    ) -> None:
        self.check_every = check_every
        self.rss_max = rss_max_mb * 1024 * 1024
        self.cpu_max = cpu_max_pct
        self._counter = 0
        self._cpu_streak = 0

    def tick(self) -> bool:
        """Chiama ogni frame. Ritorna False se il loop dovrebbe saltare il frame."""
        self._counter += 1
        if self._counter % self.check_every != 0:
            return True

        try:
            rss = _proc.memory_info().rss
            cpu = _proc.cpu_percent(interval=None)
        except psutil.Error:
            return True

        if rss > self.rss_max:
            log.warning("RSS alta (%.0f MB) — gc.collect()", rss / 1024 / 1024)
            gc.collect()

        if cpu > self.cpu_max:
            self._cpu_streak += 1
            if self._cpu_streak >= _CPU_WARN_STREAK:
                log.warning("CPU alta (%.0f%%) — throttle", cpu)
                return False
        else:
            self._cpu_streak = 0

        return True

    def force_collect(self) -> None:
        gc.collect()
