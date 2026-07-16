import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from oracletrace.runner import _is_python_launcher, execute_command, UnsupportedCommandError

REPO_ROOT = Path(__file__).resolve().parents[1]

SCRIPT = """\
def work():
    return sum(range(50_000))

def main():
    return work()

main()
"""

TEST_FILE = """\
def helper():
    return sum(range(1000))

def test_fast():
    assert helper() > 0
"""


def _run(args, cwd):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    # keep third-party pytest plugins on the host machine out of the
    # inner pytest.main run — they aren't part of what's being tested
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "oracletrace", "run", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )


class TestPythonScriptForm:
    def test_python_script(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "script.py").write_text(SCRIPT, encoding="utf-8")
            result = _run(["--", "python", "script.py"], cwd=tmp)
        assert result.returncode == 0, result.stderr
        assert "work" in result.stdout

    def test_bare_script_shorthand(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "script.py").write_text(SCRIPT, encoding="utf-8")
            result = _run(["--", "script.py"], cwd=tmp)
        assert result.returncode == 0, result.stderr
        assert "work" in result.stdout

    def test_script_args_reach_the_script(self):
        code = "import sys\nprint('ARGS:' + ','.join(sys.argv[1:]))\n"
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "script.py").write_text(code, encoding="utf-8")
            result = _run(["--", "python", "script.py", "alpha", "beta"], cwd=tmp)
        assert result.returncode == 0, result.stderr
        assert "ARGS:alpha,beta" in result.stdout

    def test_exit_code_propagates(self):
        code = SCRIPT + "import sys\nsys.exit(5)\n"
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "script.py").write_text(code, encoding="utf-8")
            result = _run(["--", "python", "script.py"], cwd=tmp)
        assert result.returncode == 5, result.stderr
        assert "work" in result.stdout  # trace still reported

    def test_json_export_works(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "script.py").write_text(SCRIPT, encoding="utf-8")
            result = _run(["--json", "t.json", "--", "python", "script.py"], cwd=tmp)
            trace = Path(tmp) / "t.json"
            assert trace.exists(), result.stderr
            assert "work" in trace.read_text(encoding="utf-8")
        assert result.returncode == 0

    def test_missing_script_fails_cleanly(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            result = _run(["--", "python", "ghost.py"], cwd=tmp)
        assert result.returncode == 1
        assert "script not found" in result.stderr


class TestModuleForm:
    def test_python_dash_m_module(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "myjob.py").write_text(SCRIPT, encoding="utf-8")
            result = _run(["--", "python", "-m", "myjob"], cwd=tmp)
        assert result.returncode == 0, result.stderr
        assert "work" in result.stdout

    def test_dash_m_shorthand(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "myjob.py").write_text(SCRIPT, encoding="utf-8")
            result = _run(["--", "-m", "myjob"], cwd=tmp)
        assert result.returncode == 0, result.stderr
        assert "work" in result.stdout


class TestPytestForm:
    def test_pytest_still_works(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "test_fast.py").write_text(TEST_FILE, encoding="utf-8")
            result = _run(["--", "pytest", "test_fast.py", "-p", "no:cacheprovider"], cwd=tmp)
        assert result.returncode == 0, result.stderr + result.stdout
        assert "1 passed" in result.stdout


class TestRejections:
    def test_non_python_binary_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            result = _run(["--", "node", "app.js"], cwd=tmp)
        assert result.returncode == 1
        assert "cannot trace" in result.stderr

    def test_python_dash_c_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            result = _run(["--", "python", "-c", "print(1)"], cwd=tmp)
        assert result.returncode == 1
        assert "not supported" in result.stderr

    def test_bare_python_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            result = _run(["--", "python"], cwd=tmp)
        assert result.returncode == 1
        assert "interactive interpreter" in result.stderr


class TestLauncherDetection:
    @pytest.mark.parametrize("token", [
        "python", "python3", "python3.12", "py",
        "python.exe", "PYTHON3.EXE", "/usr/bin/python3",
        "C:\\Python311\\python.exe",
    ])
    def test_python_launchers_recognized(self, token):
        assert _is_python_launcher(token)

    @pytest.mark.parametrize("token", ["node", "cargo", "make", "pypy-lookalike.js"])
    def test_non_python_not_recognized(self, token):
        assert not _is_python_launcher(token)


class TestExecuteCommandUnit:
    def test_empty_command_raises(self):
        with pytest.raises(UnsupportedCommandError, match="no command"):
            execute_command([])

    def test_dash_m_without_module_raises(self):
        with pytest.raises(UnsupportedCommandError, match="requires a module name"):
            execute_command(["-m"])

    def test_argv_restored_after_run(self, tmp_path, monkeypatch):
        monkeypatch.chdir(REPO_ROOT)  # same drive as the package
        script = REPO_ROOT / "_argv_check_tmp.py"
        script.write_text("pass\n", encoding="utf-8")
        try:
            before = list(sys.argv)
            execute_command(["python", str(script)])
            assert sys.argv == before
        finally:
            script.unlink()
