"""ShowdownMode — implementazione per modalità Showdown Solo/Duo.

Pedro: completa i metodi marcati con TODO.
Davide: ha definito l'ABC in base.py e l'architettura in behavior_engine.py.
"""
from __future__ import annotations

from game_state import FrameState
from game_modes.base import GameMode


class ShowdownMode(GameMode):
    """Logica specifica Showdown Solo.

    Fasi:
      EARLY  → farm cubi ai bordi, evita centro
      MID    → ambush selettivi con vantaggio cubes
      LATE   → deathmatch, third-party
    """

    @property
    def name(self) -> str:
        return "showdown"

    def preprocess(self, state: FrameState) -> FrameState:
        """Pre-processa FrameState per Showdown.

        TODO Pedro:
          - Filtra nemici fuori dalla safe zone quando in late game
          - Aggiorna cubes_self se hai detection del contatore (Fase 2.3 ML)
          - Imposta players_left da OCR counter (Fase 2 full feature)
        """
        # Placeholder: al momento ritorna state invariato.
        # BehaviorEngine → StateMachine usa game_phase già impostato da detect_all().
        return state
