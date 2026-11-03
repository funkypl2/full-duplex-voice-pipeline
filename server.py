"""
FastAPI & WebSocket Server for Full-Duplex Voice Dialogue.
"""
from __future__ import annotations
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from core.orchestrator import FullDuplexOrchestrator

app = FastAPI(title="Full-Duplex Voice Gateway")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "full-duplex-voice-pipeline"}


@app.websocket("/ws/duplex")
async def websocket_duplex_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def client_log(msg: str):
        try:
            await websocket.send_text(json.dumps({"type": "log", "message": msg}))
        except Exception:
            pass

    orchestrator = FullDuplexOrchestrator(on_log=lambda m: asyncio.create_task(client_log(m)))

    try:
        await websocket.send_text(json.dumps({
            "type": "ready",
            "message": "Full-duplex voice stream connected. Ready for simultaneous speech and interruption."
        }))

        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)
            msg_type = data.get("type")

            if msg_type == "user_speech_start":
                await orchestrator.trigger_user_speech_start()
            elif msg_type == "user_speech_end":
                text = data.get("text", "")
                await orchestrator.trigger_user_speech_end(text)
            elif msg_type == "barge_in":
                orchestrator.arbiter.trigger_barge_in()
            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        orchestrator.cancel_event.set()
    except Exception as e:
        orchestrator.cancel_event.set()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
