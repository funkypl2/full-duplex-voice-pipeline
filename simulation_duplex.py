"""
End-to-End Simulation of Full-Duplex Voice Dialogue with Mid-Sentence Barge-In Interruption.
"""
from __future__ import annotations
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import asyncio
from core.orchestrator import FullDuplexOrchestrator
from core.state_machine import DuplexState


async def run_simulation():
    print("=====================================================================")
    print("      Full-Duplex Voice Pipeline: Interactive Turn & Barge-In Demo    ")
    print("=====================================================================")

    logs = []
    def logger(msg: str):
        print(f"[*] {msg}")
        logs.append(msg)

    orchestrator = FullDuplexOrchestrator(on_log=logger)

    print("\n--- Scenario 1: Normal Conversational Turn (No Interruption) ---")
    await orchestrator.trigger_user_speech_start()
    await asyncio.sleep(0.1)
    await orchestrator.trigger_user_speech_end("请简要说明什么是全双工语音交互？")

    # Let the agent speak and finish completely
    await asyncio.sleep(2.0)
    print(f"State after normal completion: {orchestrator.state_machine.current_state.value}")

    print("\n--- Scenario 2: User Interrupts Mid-Sentence (Barge-In) ---")
    await orchestrator.trigger_user_speech_start()
    await asyncio.sleep(0.1)
    await orchestrator.trigger_user_speech_end("请详细展开讲讲全双工架构的底层技术原理？")

    # Wait until agent transitions to SPEAKING and speaks first sentence
    print("[Simulation] Waiting for Agent to begin speaking...")
    for _ in range(20):
        if orchestrator.state_machine.current_state == DuplexState.SPEAKING:
            break
        await asyncio.sleep(0.05)

    print(f"[Simulation] Agent is now in {orchestrator.state_machine.current_state.value} state!")
    print("[Simulation] >>> USER BARGES IN: '等一下，我先问个别的问题！' <<<")

    # Trigger user speech while agent is speaking
    await orchestrator.trigger_user_speech_start()
    await asyncio.sleep(0.05)

    print(f"[Simulation] State after barge-in: {orchestrator.state_machine.current_state.value}")
    print(f"[Simulation] Total Barge-in Interruption Count: {orchestrator.arbiter.interruption_count}")

    # Immediately feed the new interrupting question
    await orchestrator.trigger_user_speech_end("北京今天天气怎么样？")
    await asyncio.sleep(1.5)

    print("\n=====================================================================")
    print("      Full-Duplex Interactive Simulation Completed Successfully!     ")
    print("=====================================================================")


def main():
    asyncio.run(run_simulation())


if __name__ == "__main__":
    main()
