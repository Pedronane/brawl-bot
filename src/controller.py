import time

import pyautogui
import pydirectinput
import win32con
import win32gui

from config import CONTROL_MODE, JOYSTICK_DRAG_RADIUS, JOYSTICK_X, JOYSTICK_Y
from randomizer import keystroke_gap, maybe_human_pause

# FAILSAFE disabilitato intenzionalmente: il bot muove il mouse liberamente.
# Kill switch alternativo: crea il file "kill.flag" nella cwd per fermare il bot.
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False
pydirectinput.PAUSE = 0

_KEYS = {"w", "a", "s", "d"}
_active_keys: set[str] = set()
_joystick_down = False
_win_rect: tuple[int, int, int, int] | None = None
_hwnd: int | None = None


def set_window_rect(rect: tuple[int, int, int, int], hwnd: int | None = None) -> None:
    global _win_rect, _hwnd
    _win_rect = rect
    if hwnd is not None:
        _hwnd = hwnd


def is_window_focused() -> bool:
    if _hwnd is None:
        return True
    return win32gui.GetForegroundWindow() == _hwnd


def _ensure_focus() -> bool:
    """Porta BlueStacks in foreground se non lo è già. Ritorna True se ok."""
    if _hwnd is None:
        return True
    if win32gui.GetForegroundWindow() == _hwnd:
        return True
    try:
        win32gui.ShowWindow(_hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(_hwnd)
        time.sleep(0.05)
        return win32gui.GetForegroundWindow() == _hwnd
    except Exception:
        return False


def reset_all_inputs() -> None:
    """Rilascia tutti i tasti e il mouse — chiamare sempre su crash/exit."""
    global _active_keys, _joystick_down
    for k in list(_active_keys):
        try:
            pydirectinput.keyUp(k)
        except Exception:
            pass
    _active_keys.clear()
    if _joystick_down:
        try:
            pyautogui.mouseUp(button="left")
        except Exception:
            pass
        _joystick_down = False


# ── Keyboard mode ──────────────────────────────────────────────────────────────

def _sync_keys(target: set[str]) -> None:
    global _active_keys
    for k in _active_keys - target:
        pydirectinput.keyUp(k)
        time.sleep(keystroke_gap())
    for k in target - _active_keys:
        pydirectinput.keyDown(k)
        time.sleep(keystroke_gap())
    _active_keys = target.copy()


def _dir_to_keys(dx: float, dy: float) -> set[str]:
    keys: set[str] = set()
    if dy < -0.25:
        keys.add("w")
    elif dy > 0.25:
        keys.add("s")
    if dx < -0.25:
        keys.add("a")
    elif dx > 0.25:
        keys.add("d")
    return keys


# ── Mouse joystick mode ────────────────────────────────────────────────────────

def _joystick_center() -> tuple[int, int]:
    assert _win_rect, "call set_window_rect first"
    left, top, w, h = _win_rect
    return left + int(w * JOYSTICK_X), top + int(h * JOYSTICK_Y)


def _mouse_move(dx: float, dy: float) -> None:
    global _joystick_down
    jx, jy = _joystick_center()
    tx = jx + int(dx * JOYSTICK_DRAG_RADIUS)
    ty = jy + int(dy * JOYSTICK_DRAG_RADIUS)
    if not _joystick_down:
        pyautogui.mouseDown(jx, jy, button="left")
        _joystick_down = True
        time.sleep(0.04)
    pyautogui.moveTo(tx, ty)


def _mouse_stop() -> None:
    global _joystick_down
    if _joystick_down:
        pyautogui.mouseUp(button="left")
        _joystick_down = False


# ── Public API ─────────────────────────────────────────────────────────────────

def move(dx: float, dy: float) -> None:
    if not _ensure_focus():
        stop()
        return
    maybe_human_pause()
    if CONTROL_MODE == "keyboard":
        _sync_keys(_dir_to_keys(dx, dy))
    else:
        _mouse_move(dx, dy)


def stop() -> None:
    if CONTROL_MODE == "keyboard":
        _sync_keys(set())
    else:
        _mouse_stop()
