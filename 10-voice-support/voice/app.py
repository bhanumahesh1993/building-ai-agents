# voice/app.py
from __future__ import annotations

import asyncio
import json
import queue

from fastapi import FastAPI, WebSocket

from .agent import run_turn
from .session import Session, Turn
from .stt import TurnBuffer, transcribe, voice_detected
from .tts import synthesize

app = FastAPI(title="Voice Support Agent")


@app.websocket("/call")
async def call(ws: WebSocket):
    await ws.accept()
    session = Session()
    buf = TurnBuffer()
    audio_q: queue.Queue = queue.Queue()
    sender = asyncio.create_task(_drain(ws, audio_q))

    try:
        while True:
            msg = await ws.receive()
            if msg.get("bytes") is not None:
                await _on_frame(
                    ws, session, buf, audio_q,
                    msg["bytes"])
            elif msg.get("text") is not None:
                evt = json.loads(msg["text"])
                if evt.get("event") == "hangup":
                    break
    finally:
        audio_q.put(None)
        await sender


async def _drain(ws: WebSocket, q: queue.Queue):
    """Forward queued audio chunks to the socket."""
    while True:
        item = await asyncio.to_thread(q.get)
        if item is None:
            return
        _gen, data = item
        await ws.send_bytes(data)


async def _on_frame(ws, session, buf, audio_q, frame):
    if session.state == Turn.SPEAKING and \
            voice_detected(frame):
        session.barge_in()
        while not audio_q.empty():
            audio_q.get_nowait()
        await ws.send_json({"event": "barge_in"})
    if buf.push(frame):
        await _handle_turn(ws, session, buf, audio_q)


async def _handle_turn(ws, session, buf, audio_q):
    pcm = buf.reset()
    text, stt_ms = transcribe(pcm)
    if not text:
        session.state = Turn.LISTENING
        return
    await ws.send_json({
        "event": "transcript", "text": text,
        "stt_ms": round(stt_ms)})

    gen = session.start_turn(Turn.THINKING)
    session.history.append(
        {"role": "user", "content": text})

    def on_sentence(sentence: str):
        session.state = Turn.SPEAKING
        for chunk in synthesize(sentence):
            if not session.is_current(gen):
                return
            audio_q.put((gen, chunk))

    _, session.history = await asyncio.to_thread(
        run_turn, session.history, on_sentence)
    if session.is_current(gen):
        session.state = Turn.LISTENING
