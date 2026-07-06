import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_module(*args, cwd):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "oracletrace", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )


def test_python_dash_m_runs_the_cli():
    result = _run_module("--help", cwd=REPO_ROOT)
    assert result.returncode == 0
    assert "usage: oracletrace" in result.stdout


def test_python_dash_m_traces_a_script():
    # under the repo root so the script shares a drive with the package
    # (tracing across Windows drives is a separate, pre-existing issue)
    with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
        script = Path(tmp) / "script.py"
        script.write_text("def work():\n    return 1\n\nwork()\n", encoding="utf-8")
        result = _run_module("script.py", cwd=tmp)
    assert result.returncode == 0
    assert "work" in result.stdout
