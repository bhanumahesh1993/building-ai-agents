# tests/conftest.py
from __future__ import annotations


class FakeAnthropicResponse:
    """Stand-in for a ChatAnthropic .invoke() return value."""

    def __init__(self, content: str) -> None:
        self.content = content


class FakeLLM:
    """Deterministic stand-in for ChatAnthropic — same prompt
    always yields the same canned JSON, so tests never touch
    the network or need an API key."""

    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[str] = []

    def invoke(self, prompt: str) -> FakeAnthropicResponse:
        self.calls.append(prompt)
        return FakeAnthropicResponse(self._content)
