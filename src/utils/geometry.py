import math


def normalize(dx: float, dy: float) -> tuple[float, float]:
    mag = math.hypot(dx, dy)
    if mag < 1e-6:
        return 0.0, 0.0
    return dx / mag, dy / mag


def rotate(dx: float, dy: float, degrees: float) -> tuple[float, float]:
    r = math.radians(degrees)
    return (
        dx * math.cos(r) - dy * math.sin(r),
        dx * math.sin(r) + dy * math.cos(r),
    )


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def angle_between(dx1: float, dy1: float, dx2: float, dy2: float) -> float:
    cos_a = dx1 * dx2 + dy1 * dy2
    denom = math.hypot(dx1, dy1) * math.hypot(dx2, dy2) + 1e-9
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_a / denom))))
