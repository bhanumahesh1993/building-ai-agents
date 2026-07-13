# voice/agent.py
from __future__ import annotations

import os
import re

import anthropic

from .tools import TOOL_SCHEMAS, run_tool

MODEL = os.getenv("AGENT_MODEL", "claude-sonnet-4-5")
MAX_TOOL_HOPS = 3

SYSTEM = """You are a support agent on a phone call.
Speak in short, natural sentences -- this is voice,
not chat. Use get_order_status and search_faq to
answer; never guess an order status or a policy.
If you are not confident, say so and offer a human
transfer instead of inventing an answer."""

_client: anthropic.Anthropic | None = None
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _get_client() -> anthropic.Anthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def run_turn(history: list[dict], on_sentence):
    """Run one tool-use turn, streaming sentences out.

    `on_sentence(text)` fires as soon as a full sentence
    is ready, so TTS can start before the model is done.
    """
    messages = list(history)
    final_text = ""

    for _ in range(MAX_TOOL_HOPS):
        buffer = ""
        with _get_client().messages.stream(
            model=MODEL, max_tokens=400,
            system=SYSTEM, tools=TOOL_SCHEMAS,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                buffer += text
                final_text += text
                parts = _SENTENCE_END.split(buffer)
                for sentence in parts[:-1]:
                    if sentence.strip():
                        on_sentence(sentence.strip())
                buffer = parts[-1]
            resp = stream.get_final_message()

        messages.append({
            "role": "assistant",
            "content": resp.content})
        tool_calls = [
            b for b in resp.content
            if b.type == "tool_use"]

        if not tool_calls:
            if buffer.strip():
                on_sentence(buffer.strip())
            break

        results = [{
            "type": "tool_result",
            "tool_use_id": call.id,
            "content": str(run_tool(
                call.name, call.input)),
        } for call in tool_calls]
        messages.append({
            "role": "user", "content": results})

    return final_text, messages
