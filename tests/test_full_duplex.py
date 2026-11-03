"""
Unit tests for Full-Duplex Voice Pipeline.
"""
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pytest
import asyncio
from core.state_machine import DuplexStateMachine, DuplexState
from arbiter.barge_in import BargeInArbiter
from pipeline.audio_buffer import AsyncAudioBuffer
from core.orchestrator import FullDuplexOrchestrator


def test_state_machine_transitions():
    fsm = DuplexStateMachine()
    assert fsm.current_state == DuplexState.IDLE

    fsm.transition_to(DuplexState.LISTENING)
    assert fsm.current_state == DuplexState.LISTENING
    assert fsm.is_listening()

    fsm.transition_to(DuplexState.SPEAKING)
    assert fsm.is_speaking()


def test_audio_buffer_flush():
    buf = AsyncAudioBuffer()
    # Synchronously populate queue via loop
    async def _test():
        await buf.put(b"chunk1")
        await buf.put(b"chunk2")
        await buf.put(b"chunk3")
        assert not buf.empty()
        dropped = buf.flush()
        assert dropped == 3
        assert buf.empty()

    asyncio.run(_test())


def test_barge_in_arbiter_trigger():
    async def _test():
        fsm = DuplexStateMachine()
        cancel_event = asyncio.Event()
        flushed = []

        def flush_cb():
            flushed.append(True)

        arbiter = BargeInArbiter(
            state_machine=fsm,
            cancel_event=cancel_event,
            flush_audio_callback=flush_cb,
        )

        fsm.transition_to(DuplexState.SPEAKING)
        assert not cancel_event.is_set()

        # User speaks while agent is speaking
        triggered = arbiter.check_user_speech(is_user_speaking=True)
        assert triggered is True
        assert cancel_event.is_set()
        assert len(flushed) == 1
        assert arbiter.interruption_count == 1
        assert fsm.current_state == DuplexState.LISTENING

    asyncio.run(_test())



def test_orchestrator_pipeline_flow():
    async def _test_orch():
        orch = FullDuplexOrchestrator()
        await orch.trigger_user_speech_start()
        assert orch.state_machine.current_state == DuplexState.LISTENING
        await orch.trigger_user_speech_end("测试全双工流程")
        assert orch.state_machine.current_state in (DuplexState.THINKING, DuplexState.SPEAKING)
        # Trigger barge-in
        await orch.trigger_user_speech_start()
        assert orch.arbiter.interruption_count == 1

    asyncio.run(_test_orch())
