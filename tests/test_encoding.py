import os
import subprocess
import sys
import tempfile
from pathlib import Path

from oracletrace.tracer import _safe_char

REPO_ROOT = Path(__file__).resolve().parents[1]

RECURSIVE_SCRIPT = """\
def rec(n):
    if n:
        rec(n - 1)

def main():
    rec(3)

main()
"""


class _FakeStdout:
    def __init__(self, encoding):
        self.encoding = encoding


def test_safe_char_keeps_unicode_when_encodable(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _FakeStdout("utf-8"))
    assert _safe_char("↻", "@") == "↻"


def test_safe_char_falls_back_on_cp1252(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _FakeStdout("cp1252"))
    assert _safe_char("↻", "@") == "@"
    assert _safe_char("→", "->") == "->"


def test_safe_char_survives_missing_encoding(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _FakeStdout(None))
    assert _safe_char("→", "->") == "→"  # falls back to utf-8


def test_piped_cp1252_output_does_not_crash():
    # Piped output on Windows often defaults to cp1252, which cannot encode
    # the recursion marker in the call tree; the run then dies with
    # UnicodeEncodeError AFTER tracing succeeded. Forced via PYTHONIOENCODING
    # so the regression is caught on any platform.
    env = {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT),
        "PYTHONIOENCODING": "cp1252",
    }
    with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
        script = Path(tmp) / "script.py"
        script.write_text(RECURSIVE_SCRIPT, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "oracletrace", "script.py"],
            capture_output=True,
            text=True,
            cwd=tmp,
            env=env,
        )
    assert result.returncode == 0, result.stderr
    assert "UnicodeEncodeError" not in result.stderr
    assert "rec" in result.stdout
