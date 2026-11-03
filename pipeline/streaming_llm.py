"""
Async Streaming LLM generator with cooperative cancellation support.
"""
from __future__ import annotations
import asyncio
import re
from typing import AsyncGenerator, List, Dict, Optional


class StreamingLLMGenerator:
    """Async streaming LLM caller supporting immediate interruption via cancellation event."""

    def __init__(
        self,
        api_base: str = "http://localhost:11434/v1",
        model: str = "qwen2.5:7b",
    ):
        self.api_base = api_base
        self.model = model

    async def generate_stream(
        self,
        prompt: str,
        cancel_event: asyncio.Event,
    ) -> AsyncGenerator[str, None]:
        """
        Stream tokens asynchronously. Checks cancel_event between every token.
        """
        # Predefined rich response chunks for demonstration
        simulated_tokens = [
            "全双工", "语音", "交互的", "最大特点", "是支持", "双向同时", "通话。",
            "在传统的", "半双工模式下，", "必须等一方", "说完话并挂起，", "另一方", "才能发声。",
            "而在全双工链路中，", "你可以随时", "插话打断我，", "系统会在 50 毫秒内", "响应打断，",
            "并立即", "清空播放缓冲区，", "无缝切换到", "新的倾听状态！"
        ]

        for token in simulated_tokens:
            if cancel_event.is_set():
                # Interruption detected! Immediately break generator
                break

            yield token
            # Simulate real LLM token generation interval (30ms ~ 50ms)
            await asyncio.sleep(0.04)
