"""
Full-Duplex Voice Orchestrator.
Coordinates concurrent Audio I/O, VAD, ASR, LLM, TTS and Barge-in cancellation.
"""
from __future__ import annotations
import asyncio
import re
from typing import Callable, Optional, List
from core.state_machine import DuplexStateMachine, DuplexState
from arbiter.barge_in import BargeInArbiter
from pipeline.audio_buffer import AsyncAudioBuffer
from pipeline.streaming_llm import StreamingLLMGenerator
from pipeline.streaming_tts import StreamingTTSPlayer


class FullDuplexOrchestrator:
    """Central orchestrator managing full-duplex conversational tasks and state transitions."""

    def __init__(
        self,
        on_log: Optional[Callable[[str], None]] = None,
    ):
        self.on_log = on_log or (lambda msg: None)
        self.cancel_event = asyncio.Event()
        self.state_machine = DuplexStateMachine(on_state_change=self._on_state_change)
        self.audio_buffer = AsyncAudioBuffer()
        self.llm = StreamingLLMGenerator()
        self.tts = StreamingTTSPlayer()
        self.arbiter = BargeInArbiter(
            state_machine=self.state_machine,
            cancel_event=self.cancel_event,
            flush_audio_callback=self._flush_playback,
            on_barge_in=self._on_barge_in_event,
        )
        self.dialogue_history: List[dict] = []
        self._current_gen_task: Optional[asyncio.Task] = None

    def _log(self, text: str) -> None:
        self.on_log(text)

    def _on_state_change(self, old_state: DuplexState, new_state: DuplexState) -> None:
        self._log(f"[FSM] State changed: {old_state.value} -> {new_state.value}")

    def _flush_playback(self) -> None:
        dropped = self.audio_buffer.flush()
        self._log(f"[Arbiter] Audio buffer drained ({dropped} chunks dropped)")

    def _on_barge_in_event(self) -> None:
        self._log(f"[Arbiter] *** BARGE-IN DETECTED *** Interruption #{self.arbiter.interruption_count}")

    async def trigger_user_speech_start(self) -> None:
        """Called when VAD detects user begins speaking."""
        # Check if this acts as a barge-in interruption
        if self.state_machine.current_state in (DuplexState.SPEAKING, DuplexState.THINKING):
            self.arbiter.trigger_barge_in()
        else:
            self.state_machine.transition_to(DuplexState.LISTENING)

    async def trigger_user_speech_end(self, user_text: str) -> None:
        """Called when VAD detects user finished speaking."""
        self._log(f"[User Input]: {user_text}")
        self.dialogue_history.append({"role": "user", "content": user_text})

        # Cancel any previous hanging generation
        self.cancel_event.set()
        await asyncio.sleep(0.01)
        self.cancel_event.clear()

        # Start response generation task
        self.state_machine.transition_to(DuplexState.THINKING)
        self._current_gen_task = asyncio.create_task(self._run_generation_pipeline(user_text))

    async def _run_generation_pipeline(self, prompt: str) -> None:
        """Streams LLM tokens, chunks by sentence, synthesizes audio and pushes to buffer."""
        punct_pattern = re.compile(r"([。！？!?；;\n]+)")
        buffer_text = ""
        full_reply = ""
        first_sentence = True

        async for token in self.llm.generate_stream(prompt, self.cancel_event):
            if self.cancel_event.is_set():
                self._log("[Pipeline] Generation aborted by cancellation event.")
                break

            buffer_text += token
            full_reply += token

            parts = punct_pattern.split(buffer_text)
            if len(parts) > 1:
                while len(parts) >= 2:
                    sentence = parts.pop(0) + parts.pop(0)
                    sentence = sentence.strip()
                    if sentence:
                        if first_sentence:
                            self.state_machine.transition_to(DuplexState.SPEAKING)
                            first_sentence = False

                        self._log(f"[Agent Speaking]: {sentence}")
                        audio_chunk = await self.tts.synthesize_sentence_chunk(sentence, self.cancel_event)
                        if audio_chunk and not self.cancel_event.is_set():
                            await self.audio_buffer.put(audio_chunk)

                buffer_text = parts[0] if parts else ""

        # Flush remaining buffer text
        if buffer_text.strip() and not self.cancel_event.is_set():
            if first_sentence:
                self.state_machine.transition_to(DuplexState.SPEAKING)
            self._log(f"[Agent Speaking]: {buffer_text.strip()}")
            audio_chunk = await self.tts.synthesize_sentence_chunk(buffer_text.strip(), self.cancel_event)
            if audio_chunk and not self.cancel_event.is_set():
                await self.audio_buffer.put(audio_chunk)

        if not self.cancel_event.is_set():
            # Wait for audio playback buffer to drain
            while not self.audio_buffer.empty():
                if self.cancel_event.is_set():
                    break
                await asyncio.sleep(0.05)

            if not self.cancel_event.is_set():
                self.state_machine.transition_to(DuplexState.IDLE)
                self._log("[Pipeline] Turn finished normally.")
                self.dialogue_history.append({"role": "assistant", "content": full_reply})
