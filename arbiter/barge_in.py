"""
Barge-in Interruption Arbiter.
Monitors user speech activity while agent is generating or speaking, triggering instant interruption.
"""
from __future__ import annotations
import asyncio
from typing import Callable, Optional
from core.state_machine import DuplexStateMachine, DuplexState


class BargeInArbiter:
    """Detects user interruptions and coordinates cancellation of LLM and Audio queues."""

    def __init__(
        self,
        state_machine: DuplexStateMachine,
        cancel_event: asyncio.Event,
        flush_audio_callback: Callable[[], None],
        on_barge_in: Optional[Callable[[], None]] = None,
    ):
        self.state_machine = state_machine
        self.cancel_event = cancel_event
        self.flush_audio = flush_audio_callback
        self.on_barge_in = on_barge_in
        self.interruption_count = 0

    def check_user_speech(self, is_user_speaking: bool) -> bool:
        """
        Called on every audio frame / VAD packet.
        If user starts speaking while agent is SPEAKING or THINKING, trigger immediate barge-in.
        """
        if not is_user_speaking:
            return False

        if self.state_machine.current_state in (DuplexState.SPEAKING, DuplexState.THINKING):
            self.trigger_barge_in()
            return True

        return False

    def trigger_barge_in(self) -> None:
        """Perform instant cancellation and state transition."""
        self.interruption_count += 1
        # 1. Signal cancellation token to stop LLM generator
        self.cancel_event.set()

        # 2. Immediately flush speaker audio queue buffer
        self.flush_audio()

        # 3. Transition state to INTERRUPTED
        self.state_machine.transition_to(DuplexState.INTERRUPTED, reason="User Barge-In")

        # 4. Trigger external callback
        if self.on_barge_in:
            self.on_barge_in()

        # Move to LISTENING to capture new user speech
        self.state_machine.transition_to(DuplexState.LISTENING, reason="Capturing new speech")
