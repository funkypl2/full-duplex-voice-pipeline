"""
Streaming sentence-level TTS synthesizer for full-duplex pipelines.
"""
from __future__ import annotations
import asyncio
import io
import struct
import numpy as np
from typing import AsyncGenerator, Optional


class StreamingTTSPlayer:
    """Converts text sentences to audio chunks on the fly with cancellation support."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    async def synthesize_sentence_chunk(
        self,
        sentence: str,
        cancel_event: asyncio.Event,
    ) -> Optional[bytes]:
        """Synthesize a short audio byte block for a single sentence."""
        if cancel_event.is_set() or not sentence.strip():
            return None

        # Generate lightweight audio representation (0.3s gentle tone per sentence)
        duration = 0.3
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        waveform = (0.2 * np.sin(2 * np.pi * 500.0 * t) * 32767).astype(np.int16)

        buf = io.BytesIO()
        buf.write(b"RIFF")
        buf.write(struct.pack("<I", 36 + len(waveform) * 2))
        buf.write(b"WAVEfmt ")
        buf.write(struct.pack("<IHHIIHH", 16, 1, 1, self.sample_rate, self.sample_rate * 2, 2, 16))
        buf.write(b"data")
        buf.write(struct.pack("<I", len(waveform) * 2))
        buf.write(waveform.tobytes())

        # Yield to event loop
        await asyncio.sleep(0.02)
        if cancel_event.is_set():
            return None
        return buf.getvalue()
