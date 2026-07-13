# tests/test_imports.py
"""Guards the hardening invariant: every voice.* module must import
cleanly with no environment variables set and no model weights on
disk. Client/model construction is lazy (behind _get_* helpers),
so merely importing these modules must never touch the network,
the filesystem for model weights, or an os.environ[...] lookup that
would raise KeyError.

Runs the import in a subprocess with a scrubbed environment rather
than importlib.reload()-ing in-process: reload() re-executes a
module's code inside its *existing* namespace dict, which would
silently replace the Turn enum class out from under any test file
that already holds a reference to the pre-reload class -- breaking
enum equality elsewhere in the suite."""
from __future__ import annotations

import os
import subprocess
import sys


def test_all_voice_modules_import_without_env_vars():
    code = (
        "import voice.tools, voice.session, voice.stt, "
        "voice.tts, voice.agent, voice.app"
    )
    # Only PATH/HOME survive -- enough for the interpreter and
    # dynamic linker to start; no ANTHROPIC_API_KEY, TTS_API_KEY,
    # AGENT_MODEL, or TTS_VOICE make it through.
    minimal_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
    }
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=minimal_env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_stt_module_has_no_client_state_at_import():
    from voice import stt
    assert stt._model is None
    assert stt._vad is None


def test_agent_module_has_no_client_state_at_import():
    from voice import agent
    assert agent._client is None
