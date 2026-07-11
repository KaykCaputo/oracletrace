"""Universal in-process command execution for `oracletrace run`.

The tracer uses sys.setprofile(), which only observes the CURRENT process.
A subprocess would be invisible and traces would come back empty — so every
supported invocation is executed in-process:

    pytest [args]                    -> pytest.main([args])
    python -m <module> [args]        -> runpy.run_module()
    python <script.py> [args]        -> runpy.run_path()
    -m <module> [args]               -> runpy.run_module()
    <script.py> [args]               -> runpy.run_path()

Non-Python launchers (node, cargo, make...) are rejected with a clear error
instead of silently producing an empty trace.
"""

import os
import sys
import runpy
from contextlib import contextmanager
from typing import Iterator, List


class UnsupportedCommandError(Exception):
    pass


_PYTHON_ALIASES = {"python", "python3", "py"}


def _is_python_launcher(token: str) -> bool:
    base = os.path.basename(token).lower()
    if base.endswith(".exe"):
        base = base[:-4]
    # strip minor-versioned launchers: python3.12 -> python3
    while base and base[-1].isdigit():
        base = base[:-1]
    base = base.rstrip(".")
    return base in _PYTHON_ALIASES


@contextmanager
def _patched_argv(argv: List[str]) -> Iterator[None]:
    original = sys.argv
    sys.argv = argv
    try:
        yield
    finally:
        sys.argv = original


@contextmanager
def _prepended_path(entry: str) -> Iterator[None]:
    sys.path.insert(0, entry)
    try:
        yield
    finally:
        try:
            sys.path.remove(entry)
        except ValueError:
            pass


def _exit_code_from(exc: SystemExit) -> int:
    # Same semantics as tracing a script directly: sys.exit() -> 0,
    # sys.exit(7) -> 7, sys.exit("msg") -> message on stderr, code 1
    if exc.code is None:
        return 0
    if isinstance(exc.code, int):
        return exc.code
    print(exc.code, file=sys.stderr)
    return 1


def _run_module(module: str, args: List[str]) -> int:
    # Mirror `python -m`: cwd is importable
    with _patched_argv([module] + args), _prepended_path(os.getcwd()):
        try:
            runpy.run_module(module, run_name="__main__", alter_sys=True)
        except SystemExit as e:
            return _exit_code_from(e)
    return 0


def _run_script(script: str, args: List[str]) -> int:
    if not os.path.exists(script):
        raise UnsupportedCommandError(f"script not found: {script}")
    script = os.path.abspath(script)
    # Mirror `python script.py`: script dir is importable
    with _patched_argv([script] + args), _prepended_path(os.path.dirname(script)):
        try:
            runpy.run_path(script, run_name="__main__")
        except SystemExit as e:
            return _exit_code_from(e)
    return 0


def _run_pytest(args: List[str]) -> int:
    try:
        import pytest
    except ImportError:
        raise UnsupportedCommandError(
            "pytest is not installed. Install it with: pip install pytest"
        )
    with _patched_argv(["pytest"] + args):
        return int(pytest.main(args))


def execute_command(command: List[str]) -> int:
    """Run a command in-process, returning its exit code.

    Raises UnsupportedCommandError for invocations that cannot be traced
    in-process (non-Python binaries, `python -c`, missing scripts).
    """
    if not command:
        raise UnsupportedCommandError("no command specified")

    head, *rest = command

    if head == "pytest":
        return _run_pytest(rest)

    if head == "-m":
        if not rest:
            raise UnsupportedCommandError("'-m' requires a module name")
        return _run_module(rest[0], rest[1:])

    if _is_python_launcher(head):
        if not rest:
            raise UnsupportedCommandError(
                "interactive interpreter cannot be traced; pass a script or -m <module>"
            )
        sub, *sub_rest = rest
        if sub == "-m":
            if not sub_rest:
                raise UnsupportedCommandError("'-m' requires a module name")
            return _run_module(sub_rest[0], sub_rest[1:])
        if sub == "-c":
            raise UnsupportedCommandError(
                "'python -c' is not supported; put the code in a script file"
            )
        if sub.startswith("-"):
            raise UnsupportedCommandError(
                f"unsupported interpreter option '{sub}'; "
                "use 'python <script.py>' or 'python -m <module>'"
            )
        return _run_script(sub, sub_rest)

    if head.endswith(".py"):
        return _run_script(head, rest)

    raise UnsupportedCommandError(
        f"cannot trace '{head}' in-process. The tracer only observes the current "
        "Python process, so external binaries would produce an empty trace. "
        "Supported: pytest, python <script.py>, python -m <module>, <script.py>"
    )
