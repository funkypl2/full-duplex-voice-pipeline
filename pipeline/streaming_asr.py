"""
Streaming ASR and VAD endpointing simulation module.
"""
from __future__ import annotations
import numpy as np
from typing import AsyncGenerator, Callable, Optional


class StreamingASRAdapter:
    """Simulates or interfaces with streaming ASR (SenseVoice / FunASR / Whisper-streaming)."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.audio_accumulator = []

    def feed_chunk(self, chunk: np.ndarray) -> tuple[bool, str]:
        """
        Feed an incoming audio chunk (e.g. 50ms ~ 100ms).
        Returns:
            (is_partial_ready, partial_text)
        """
        self.audio_accumulator.append(chunk)
        total_len = sum(len(c) for c in self.audio_accumulator)
        duration_sec = total_len / self.sample_rate

        # Simple partial simulation
        if duration_sec > 1.0:
            return True, "我想了解一下..."
        return False, ""

    def finalize(self) -> str:
        """Call when speech endpoint (silence) is detected."""
        self.audio_accumulator.clear()
        return "请介绍一下全双工语音交互的核心优势和打断机制。"
