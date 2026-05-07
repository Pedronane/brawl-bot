import cv2
import mss
import numpy as np
import win32gui


def find_window(title: str) -> int | None:
    matches = []

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
    left, top, w, h = window_rect(hwnd)
    with mss.mss() as sct:
        shot = sct.grab({"top": top, "left": left, "width": w, "height": h})
        img = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
    return img, (left, top, w, h)
