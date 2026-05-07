from __future__ import annotations

from abc import ABC, abstractmethod

from game_state import FrameState


class GameMode(ABC):
    """Interface for game modes. Pedro implements concrete subclasses."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    def loop_interval_override(self) -> float | None:
        """Custom loop interval, or None to use config default."""
        return None

    def on_enter(self) -> None:
        """Called when switching into this mode."""

    def on_exit(self) -> None:
        """Called when switching out of this mode."""

    @abstractmethod
    def tick(self, state: FrameState) -> str:
        """Run one frame of mode logic. Returns current state name."""
        ...

    @abstractmethod
    def objective_reached(self, state: FrameState) -> bool:
        """True when this mode's current objective is met."""
        ...
