from __future__ import annotations

from collections import deque

import config as cfg

_WINDOW = 120  # campioni (frame)


class BehaviorEngine:
    """Adatta parametri config a runtime basandosi su metriche sessione."""

    def __init__(self) -> None:
        self._stuck:  deque[bool] = deque(maxlen=_WINDOW)
        self._enemy:  deque[bool] = deque(maxlen=_WINDOW)
        self._poison: deque[bool] = deque(maxlen=_WINDOW)

        self.avoid_angle:          float = float(cfg.AVOID_ANGLE)
        self.loop_interval:        float = float(cfg.LOOP_INTERVAL)
        self.poison_edge_fraction: float = float(cfg.POISON_EDGE_FRACTION)

        self._ticks = 0

    def record(
        self, *, stuck: bool, enemies_visible: bool, poison: bool
    ) -> None:
        self._stuck.append(stuck)
        self._enemy.append(enemies_visible)
        self._poison.append(poison)
        self._ticks += 1
        if self._ticks % 60 == 0:
            self._adapt()

    def _ratio(self, log: deque[bool]) -> float:
        return sum(log) / len(log) if log else 0.0

    def _adapt(self) -> None:
        stuck_r  = self._ratio(self._stuck)
        enemy_r  = self._ratio(self._enemy)
        poison_r = self._ratio(self._poison)

        # stuck alto → angolo deviazione più ampio
        self.avoid_angle = max(50.0, min(120.0, cfg.AVOID_ANGLE + stuck_r * 50.0))

        # nemici frequenti → loop più veloce
        self.loop_interval = max(0.04, min(0.10, cfg.LOOP_INTERVAL - enemy_r * 0.04))

        # veleno frequente → edge detection più sensibile
        self.poison_edge_fraction = max(
            0.12, min(0.28, cfg.POISON_EDGE_FRACTION + poison_r * 0.10)
        )

    @property
    def stats(self) -> dict:
        return {
            "stuck_ratio":          round(self._ratio(self._stuck),  3),
            "enemy_ratio":          round(self._ratio(self._enemy),  3),
            "poison_ratio":         round(self._ratio(self._poison), 3),
            "avoid_angle":          round(self.avoid_angle, 1),
            "loop_interval":        round(self.loop_interval, 4),
            "poison_edge_fraction": round(self.poison_edge_fraction, 4),
        }
