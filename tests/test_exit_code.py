import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

EXITING_SCRIPT = """\
import sys

def work():
    return sum(range(1000))

work()
sys.exit(7)
"""


def _run(args, cwd):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "oracletrace", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )


def test_script_exit_code_is_propagated():
    with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
        (Path(tmp) / "script.py").write_text(EXITING_SCRIPT, encoding="utf-8")
        result = _run(["script.py"], cwd=tmp)
    assert result.returncode == 7, result.stderr
    assert "work" in result.stdout  # the summary still prints


def test_exports_still_happen_after_sys_exit():
    with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
        (Path(tmp) / "script.py").write_text(EXITING_SCRIPT, encoding="utf-8")
        result = _run(["script.py", "--json", "trace.json"], cwd=tmp)
        trace = Path(tmp) / "trace.json"
        assert trace.exists(), result.stderr  # previously nothing was written
        assert "work" in trace.read_text(encoding="utf-8")
    assert result.returncode == 7


def test_sys_exit_with_message_prints_it_and_exits_1():
    script = "import sys\nsys.exit('boom')\n"
    with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
        (Path(tmp) / "script.py").write_text(script, encoding="utf-8")
        result = _run(["script.py"], cwd=tmp)
    assert result.returncode == 1
    assert "boom" in result.stderr


def test_bare_sys_exit_is_success():
    script = "def work():\n    pass\n\nwork()\nimport sys\nsys.exit()\n"
    with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
        (Path(tmp) / "script.py").write_text(script, encoding="utf-8")
        result = _run(["script.py"], cwd=tmp)
    assert result.returncode == 0, result.stderr
