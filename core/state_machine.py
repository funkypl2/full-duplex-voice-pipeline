"""
Finite State Machine (FSM) for Full-Duplex Voice Dialogue.
"""
from __future__ import annotations
from enum import Enum
from typing import Callable, List, Optional
import time


class DuplexState(str, Enum):
    IDLE = "IDLE"                         # Waiting for user interaction
    LISTENING = "LISTENING"               # User is actively speaking (VAD active)
    THINKING = "THINKING"                 # ASR completed, LLM first token pending
    SPEAKING = "SPEAKING"                 # Agent is synthesizing & playing audio output
    INTERRUPTED = "INTERRUPTED"           # User barged in while agent was speaking


class DuplexStateMachine:
    """Manages full-duplex conversational state transitions and event listeners."""

    def __init__(self, on_state_change: Optional[Callable[[DuplexState, DuplexState], None]] = None):
        self._state = DuplexState.IDLE
        self.on_state_change = on_state_change
        self.state_change_time = time.time()
        self.history: List[tuple[float, DuplexState]] = [(self.state_change_time, self._state)]

    @property
    def current_state(self) -> DuplexState:
        return self._state

    def transition_to(self, new_state: DuplexState, reason: str = "") -> None:
        if self._state == new_state:
            return

        old_state = self._state
        self._state = new_state
        self.state_change_time = time.time()
        self.history.append((self.state_change_time, self._state))

        if self.on_state_change:
            self.on_state_change(old_state, new_state)

    def is_speaking(self) -> bool:
        return self._state == DuplexState.SPEAKING

    def is_listening(self) -> bool:
        return self._state in (DuplexState.LISTENING, DuplexState.INTERRUPTED)
