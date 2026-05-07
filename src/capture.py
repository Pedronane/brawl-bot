from __future__ import annotations

import ctypes
import time

import cv2
import mss
import numpy as np
import win32gui


# ── Window discovery ───────────────────────────────────────────────────────────

def find_window(title: str) -> int | None:
    matches: list[int] = []

    def _cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            if title.lower() in win32gui.GetWindowText(hwnd).lower():
                matches.append(hwnd)

    win32gui.EnumWindows(_cb, None)
    return matches[0] if matches else None


def window_rect(hwnd: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return left, top, right - left, bottom - top


def capture(hwnd: int) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Cattura un singolo frame (crea/distrugge mss ogni volta — per uso sporadico)."""
    left, top, w, h = window_rect(hwnd)
    if w <= 0 or h <= 0:
        raise RuntimeError(f"Finestra con dimensioni invalide: {w}x{h}. BlueStacks minimizzato?")
    with mss.mss() as sct:
        shot = sct.grab({"top": top, "left": left, "width": w, "height": h})
        arr = np.array(shot)
        if arr.size == 0:
            raise RuntimeError(f"Screenshot vuoto per regione ({left},{top},{w},{h}).")
        img = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
    return img, (left, top, w, h)


def capture_with_sct(
    sct, hwnd: int
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Cattura usando istanza mss già aperta (per loop ad alta frequenza)."""
    left, top, w, h = window_rect(hwnd)
    if w <= 0 or h <= 0:
        raise RuntimeError(f"Finestra con dimensioni invalide: {w}x{h}.")
    shot = sct.grab({"top": top, "left": left, "width": w, "height": h})
    arr = np.array(shot)
    if arr.size == 0:
        raise RuntimeError(f"Screenshot vuoto per regione ({left},{top},{w},{h}).")
    img = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
    return img, (left, top, w, h)


# ── Window health monitor ──────────────────────────────────────────────────────

class WindowWatcher:
    """Controlla che BlueStacks sia visibile e non crashato.

    Chiama healthy() ogni frame; se False, main.py deve dormire e ritentare.
    """

    _SW_RESTORE = 9

    def __init__(self, title: str = "BlueStacks") -> None:
        self.title = title
        self._hwnd: int | None = None
        self._missing_streak = 0

    def healthy(self) -> tuple[bool, str]:
        """Ritorna (ok, reason). reason='' se ok."""
        hwnd = self._get_hwnd()
        if hwnd is None:
            self._missing_streak += 1
            return False, "window_missing"
        self._missing_streak = 0

        if win32gui.IsIconic(hwnd):
            self._restore(hwnd)
            return False, "minimized"

        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w, h = right - left, bottom - top
        if w < 100 or h < 100:
            return False, "too_small"

        return True, ""

    def _get_hwnd(self) -> int | None:
        if self._hwnd and win32gui.IsWindow(self._hwnd):
            return self._hwnd
        self._hwnd = find_window(self.title)
        return self._hwnd

    def _restore(self, hwnd: int) -> None:
        try:
            ctypes.windll.user32.ShowWindow(hwnd, self._SW_RESTORE)
            time.sleep(0.5)
        except Exception:
            pass
