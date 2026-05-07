"""BehaviorEngine: coordina StateMachine + GameMode + SessionLogger.

Layer intermedio tra la pipeline di detection (FrameState) e il controller.
Responsabilità:
  - Seleziona tattiche dal game_phase corrente
  - Delega il tick al game mode specifico
  - Chiama SessionLogger per transizioni e campioni
"""
from __future__ import annotations

from game_state import FrameState
from logger import SessionLogger, log
from state_machine import StateMachine
from tactics import get_tactics


class BehaviorEngine:
    """Orchestratore ad alto livello del comportamento del bot."""

    def __init__(
        self,
        state_machine: StateMachine,
        mode,                        # GameMode ABC (showdown, gem_grab, ...)
        session_logger: SessionLogger | None = None,
    ) -> None:
        self._sm = state_machine
        self._mode = mode
        self._slog = session_logger
        self._prev_state: str = ""
        self._frame_idx: int = 0

    def update(self, frame, state: FrameState, controller) -> str:
        """Tick principale. Ritorna nome stato corrente."""
        # Il game mode può pre-processare lo state (es. filtrare nemici irrilevanti)
        state = self._mode.preprocess(state)

        # Tick state machine con tactics del game mode
        current = self._sm.tick(frame, state, controller)

        # Log transizioni su DB se logger disponibile
        if self._slog is not None:
            if current != self._prev_state:
                self._slog.log_transition(
                    from_state=self._prev_state or "START",
                    to_state=current,
                    trigger=self._mode.name,
                    hp_ratio=state.hp_ratio,
                    players_left=state.players_left,
                    poison_phase=state.game_phase,
                    frame_idx=self._frame_idx,
                )
                log.info(
                    f"[{current:7s}] [{state.game_phase}] "
                    f"enemies={len(state.enemies)} "
                    f"hp={state.hp_ratio:.2f} "
                    f"cubes={state.cubes_self}"
                )
            self._slog.maybe_sample(state)

        self._prev_state = current
        self._frame_idx += 1
        return current

    @property
    def prev_state(self) -> str:
        return self._prev_state
