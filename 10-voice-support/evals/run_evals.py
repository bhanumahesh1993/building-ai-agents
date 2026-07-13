# evals/run_evals.py
from __future__ import annotations

import json
import statistics
import wave

from voice.agent import run_turn
from voice.stt import transcribe


def _load_audio(path: str) -> bytes:
    with wave.open(path, "rb") as wf:
        return wf.readframes(wf.getnframes())


def word_error_rate(ref: str, hyp: str) -> float:
    """Edit-distance WER proxy over words."""
    r, h = ref.lower().split(), hyp.lower().split()
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1, d[i][j - 1] + 1,
                d[i - 1][j - 1] + cost)
    return d[len(r)][len(h)] / max(len(r), 1)


def run_case(case: dict) -> dict:
    path = f"evals/audio/{case['audio']}"
    hyp, _ = transcribe(_load_audio(path))
    wer = word_error_rate(case["text"], hyp)

    def on_sentence(sentence: str):
        pass  # a real harness would time first_ms here

    reply, _ = run_turn(
        [{"role": "user", "content": hyp}], on_sentence)
    success = all(
        kw in reply.lower() for kw in case["kw"])
    return {"wer": round(wer, 2), "task_success": success}


if __name__ == "__main__":
    results = []
    with open("evals/calls.jsonl") as fh:
        for line in fh:
            results.append(run_case(json.loads(line)))
    print("mean WER:", statistics.mean(
        r["wer"] for r in results))
    print("task success rate:", statistics.mean(
        int(r["task_success"]) for r in results))
