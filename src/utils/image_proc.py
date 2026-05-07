"""Temporal filtering, frame sanity checks, perceptual hashing."""
from __future__ import annotations

import math
from collections import deque

import cv2
import numpy as np


class TemporalFilter:
    """Conferma detections solo se compaiono in ≥threshold frame su window.

    Riduce falsi positivi ~80% su HP-bar enemies. Thread-unsafe (usa in un
    solo thread — DetectThread).
    """

    def __init__(self, window: int = 3, radius: int = 40, threshold: int = 2) -> None:
        self.window = window
        self.radius = radius
        self.threshold = threshold
        self._history: deque[list] = deque(maxlen=window)

    def update(self, detections: list) -> list:
        """Aggiorna history. Ritorna solo detections confermate da ≥threshold frame."""
        self._history.append(list(detections))
        if len(self._history) < self.threshold:
            return []
        return self._vote()

    def _vote(self) -> list:
        if not self._history:
            return []
        confirmed = []
        for det in self._history[-1]:
            x, y = det[0], det[1]
            votes = 1
            for prev in list(self._history)[:-1]:
                for pdet in prev:
                    if math.hypot(x - pdet[0], y - pdet[1]) <= self.radius:
                        votes += 1
                        break
            if votes >= self.threshold:
                confirmed.append(det)
        return confirmed

    def reset(self) -> None:
        self._history.clear()


class FrameSanity:
    """Rileva frame corrotti e freeze via DCT-pHash a 64 bit.

    Non richiede imagehash — usa cv2.dct su finestra 32x32.
    """

    def __init__(self, freeze_n: int = 30, hash_diff_max: int = 2) -> None:
        self.freeze_n = freeze_n
        self.hash_diff_max = hash_diff_max
        self._last_hash: int | None = None
        self._freeze_count: int = 0

    def check(self, frame: np.ndarray) -> tuple[bool, str]:
        """Verifica se il frame è valido.

        Returns:
            (ok, reason) — ok=False se frame sospetto.
        """
        h, w = frame.shape[:2]
        if h < 100 or w < 100:
            return False, "wrong_dims"
        if float(frame.std()) < 1.0:
            return False, "monochrome"

        ph = _phash(frame)
        if self._last_hash is not None:
            diff = bin(ph ^ self._last_hash).count("1")
            if diff <= self.hash_diff_max:
                self._freeze_count += 1
            else:
                self._freeze_count = 0
        self._last_hash = ph

        if self._freeze_count >= self.freeze_n:
            return False, f"freeze_{self._freeze_count}"
        return True, "ok"

    def reset(self) -> None:
        self._last_hash = None
        self._freeze_count = 0


def _phash(frame: np.ndarray) -> int:
    """DCT-based 64-bit pHash su frame BGR. Nessuna dipendenza esterna."""
    small = cv2.resize(frame, (32, 32), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    dct = cv2.dct(gray)
    top = dct[:8, :8].flatten()
    mean = float(top[1:].mean())
    bits = (top > mean).astype(np.uint8)
    result = 0
    for b in bits:
        result = (result << 1) | int(b)
    return result
