"""
Thread-safe Async Audio Buffer with instant flush support.
"""
from __future__ import annotations
import asyncio
import numpy as np
from typing import Optional, List


class AsyncAudioBuffer:
    """Queue for streaming audio chunks with instantaneous flush capability."""

    def __init__(self, maxsize: int = 50):
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=maxsize)

    async def put(self, chunk: bytes) -> None:
        await self._queue.put(chunk)

    async def get(self) -> bytes:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    def empty(self) -> bool:
        return self._queue.empty()

    def flush(self) -> int:
        """Immediately drop all pending audio chunks in queue."""
        dropped = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
                dropped += 1
            except (asyncio.QueueEmpty, ValueError):
                break
        return dropped
