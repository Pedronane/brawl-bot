"""Pipeline 3-thread: CaptureThread → frame_slot → DetectThread → state_slot → Main.

Pattern "always-latest": producer mai blocca, consumer ottiene sempre frame più recente.
Drop aggressivo frame stale > stale_ms ms.
"""
from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Generic, TypeVar

# Lazy imports: capture/mss/detector richiedono win32gui (Windows-only).
# Importati solo dentro run() così il modulo è importabile su Linux per i test.
if TYPE_CHECKING:
    from capture import WindowWatcher
    from utils.image_proc import FrameSanity

try:
    from logger import log
except Exception:  # noqa: BLE001
    import logging as log  # type: ignore[assignment]

T = TypeVar("T")


class LatestSlot(Generic[T]):
    """Buffer a singolo slot thread-safe.

    - put(): mai blocca, sovrascrive il valore precedente.
    - get(): blocca finché non arriva un valore nuovo (o timeout).
    - peek(): lettura non bloccante dell'ultimo valore (può essere None).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._item: tuple[T, float, int] | None = None
        self._seq: int = 0

    def put(self, value: T) -> None:
        with self._lock:
            self._seq += 1
            self._item = (value, time.monotonic(), self._seq)
        self._event.set()

    def get(self, timeout: float = 1.0) -> tuple[T, float, int] | None:
        """Blocca fino a nuovo valore o timeout. Ritorna (value, ts, seq) o None."""
        if not self._event.wait(timeout):
            return None
        with self._lock:
            item = self._item
            self._event.clear()
        return item

    def peek(self) -> tuple[T, float, int] | None:
        """Non-bloccante: ritorna ultimo (value, ts, seq) o None."""
        with self._lock:
            return self._item


class CaptureThread(threading.Thread):
    """Cattura frame da BlueStacks a target_fps e li pubblica su frame_slot.

    Usa un'unica istanza mss per tutta la vita del thread (performance).
    Skip frame se WindowWatcher o FrameSanity falliscono.
    """

    def __init__(
        self,
        hwnd: int,
        frame_slot: LatestSlot,
        watcher: WindowWatcher,
        sanity: FrameSanity,
        target_fps: float = 30.0,
    ) -> None:
        super().__init__(name="CaptureThread", daemon=True)
        self._hwnd = hwnd
        self._slot = frame_slot
        self._watcher = watcher
        self._sanity = sanity
        self._period = 1.0 / target_fps
        self._stop = threading.Event()
        self.frames_captured: int = 0
        self.frames_dropped: int = 0

    def run(self) -> None:
        import mss as _mss                          # lazy: win32-safe
        from capture import capture_with_sct        # lazy: win32gui

        with _mss.mss() as sct:
            next_t = time.monotonic()
            while not self._stop.is_set():
                t0 = time.monotonic()

                ok, reason = self._watcher.healthy()
                if not ok:
                    log.warning(f"[Capture] window not healthy: {reason}")
                    time.sleep(1.0)
                    next_t = time.monotonic()
                    continue

                try:
                    frame, rect = capture_with_sct(sct, self._hwnd)
                    frame_ok, sanity_reason = self._sanity.check(frame)
                    if frame_ok:
                        self._slot.put((frame, rect))
                        self.frames_captured += 1
                    else:
                        log.debug(f"[Capture] frame skip: {sanity_reason}")
                        self.frames_dropped += 1
                except Exception:
                    log.exception("[Capture] error")
                    time.sleep(0.05)

                # Pacing: deadline scheduling, no busy-wait
                next_t += self._period
                sleep = next_t - time.monotonic()
                if sleep > 0.001:
                    time.sleep(sleep)
                elif sleep < -self._period:
                    next_t = time.monotonic()   # molto in ritardo: resincronizza

    def stop(self) -> None:
        self._stop.set()


class DetectThread(threading.Thread):
    """Legge frame_slot, esegue detection, pubblica su state_slot.

    Drop frame stale (età > stale_ms): evita di lavorare su frame vecchi quando
    il detect è più lento del capture.
    """

    def __init__(
        self,
        frame_slot: LatestSlot,
        state_slot: LatestSlot,
        stale_ms: float = 80.0,
    ) -> None:
        super().__init__(name="DetectThread", daemon=True)
        self._src = frame_slot
        self._dst = state_slot
        self._stale_s = stale_ms / 1000.0
        self._stop = threading.Event()
        self.frames_detected: int = 0
        self.frames_stale: int = 0

    def run(self) -> None:
        from detector import detect_all  # lazy: evita catena win32gui

        while not self._stop.is_set():
            item = self._src.get(timeout=0.2)
            if item is None:
                continue

            (frame, rect), ts, seq = item
            age = time.monotonic() - ts
            if age > self._stale_s:
                log.debug(f"[Detect] drop stale frame age={age*1000:.0f}ms")
                self.frames_stale += 1
                continue

            try:
                state = detect_all(frame, frame_idx=self.frames_detected)
                self._dst.put((frame, state, rect))
                self.frames_detected += 1
            except Exception:
                log.exception("[Detect] error")

    def stop(self) -> None:
        self._stop.set()
