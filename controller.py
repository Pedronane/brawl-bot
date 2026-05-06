import time
import pyautogui
import pydirectinput
from config import CONTROL_MODE, JOYSTICK_X, JOYSTICK_Y, JOYSTICK_DRAG_RADIUS

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False
pydirectinput.PAUSE = 0

_KEYS = {"w", "a", "s", "d"}
_active_keys: set[str] = set()
_joystick_down = False
_win_rect: tuple[int, int, int, int] | None = None


def set_window_rect(rect: tuple[int, int, int, int]) -> None:
    global _win_rect
    _win_rect = rect


# ── Keyboard mode ──────────────────────────────────────────────────────────────

def _sync_keys(target: set[str]) -> None:
    global _active_keys
    for k in _active_keys - target:
        pydirectinput.keyUp(k)
    for k in target - _active_keys:
        pydirectinput.keyDown(k)
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
    if CONTROL_MODE == "keyboard":
        _sync_keys(_dir_to_keys(dx, dy))
    else:
        _mouse_move(dx, dy)


def stop() -> None:
    if CONTROL_MODE == "keyboard":
        _sync_keys(set())
    else:
        _mouse_stop()
