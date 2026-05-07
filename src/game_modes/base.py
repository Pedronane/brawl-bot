"""ABC per game modes — Pedro implementa le sottoclassi."""
from __future__ import annotations

from abc import ABC, abstractmethod

from game_state import FrameState


class GameMode(ABC):
    """Interfaccia base per ogni modalità di gioco."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome human-readable del mode (es. 'showdown', 'gem_grab')."""

    @abstractmethod
    def preprocess(self, state: FrameState) -> FrameState:
        """Trasforma FrameState prima del tick StateMachine.

        Usi tipici:
          - Filtrare nemici irrilevanti per il mode
          - Aggiungere context specifico (es. gem count in Gem Grab)
          - Sovrascrivere game_phase se il mode ha logica propria
        """
