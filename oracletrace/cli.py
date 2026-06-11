import re
import sys
import os
import json
import runpy
import csv
import argparse
from dataclasses import asdict
from typing import List, Dict, Any, Optional, Tuple
from re import Pattern
from argparse import ArgumentParser, Namespace
from importlib.metadata import version
from .tracer import Tracer, TracerData
from .compare import compare_traces, ComparisonData
from .reporters import generate_html_report


_MODULE_NAME: str = __name__.split(".")[0]


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "run":
        return _run_command(sys.argv[2:])
    return _run_target()


def _validate_top(top_str: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if top_str is None:
        return None, None
    try:
        top = int(top_str)
        if top < 1:
            raise ValueError
    except ValueError:
        print(f"argument --top: invalid int value: '{top_str}'", file=sys.stderr)
        return None, 1
    return top, None


def _compile_ignore_patterns(
    patterns: Optional[List[str]],
) -> Tuple[Optional[List[Pattern]], Optional[int]]:
    if not patterns:
        return [], None
    compiled: List[Pattern] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as e:
            print(f"Regex error: {pattern} -> {e}", file=sys.stderr)
            return None, 1
    return compiled, None


_BASE_PARSER: ArgumentParser = ArgumentParser(add_help=False)
_BASE_PARSER.add_argument("--json", help="Export trace result to JSON file")
_BASE_PARSER.add_argument("--csv", help="Export trace result to CSV file")
_BASE_PARSER.add_argument("--html", help="Export trace result to interactive HTML file")
_BASE_PARSER.add_argument("--compare", help="Compare against previous trace JSON")
_BASE_PARSER.add_argument(
    "--ignore",
    metavar="REGEX",
    nargs="+",
    help="Space separated list of regex patterns for keys (file path and function name) to ignore.",
)
_BASE_PARSER.add_argument(
    "--top",
    metavar="NUMBER",
    help="Limits the number of functions shown in the summary table",
)
_BASE_PARSER.add_argument(
    "--fail-on-regression",
    action="store_true",
    help="Exit with a non-zero code when regression exceeds threshold.",
)
_BASE_PARSER.add_argument(
    "--threshold",
    type=float,
    default=5.0,
    help="Regression threshold percentage used with --fail-on-regression.",
)
_BASE_PARSER.add_argument(
    "--only-regressions",
    action="store_true",
    help="Hide functions which didn't run slower than baseline. Use with --compare",
)


def _export_results(data: TracerData, args: Namespace) -> None:
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(asdict(data), f, indent=4)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer: csv.DictWriter = csv.DictWriter(
                f, fieldnames=["function", "total_time", "calls", "avg_time"]
            )
            writer.writeheader()
            for fn in data.functions:
                writer.writerow({
                    "function": fn.name,
                    "total_time": fn.total_time,
                    "calls": fn.call_count,
                    "avg_time": fn.avg_time,
                })

    if args.html:
        generate_html_report(data, args.html)
        print(f"HTML report generated: {os.path.abspath(args.html)}")


def _compare_and_fail(
    data: TracerData, args: Namespace
) -> Optional[int]:
    if not args.compare:
        return None

    if not os.path.exists(args.compare):
        print(f"Compare file not found: {args.compare}", file=sys.stderr)
        return 1

    with open(args.compare, "r", encoding="utf-8") as f:
        old_data: TracerData = TracerData.from_dict(json.load(f))

    comparison_result: ComparisonData = compare_traces(
        old_data,
        data,
        threshold=args.threshold,
        show_only_regressions=args.only_regressions,
    )

    if args.fail_on_regression and comparison_result.has_regression:
        print(
            f"Build failed: performance regression above {args.threshold:.2f}% detected.",
            file=sys.stderr,
        )
        return 2

    return None


def _init_tracer(args: Namespace) -> Tuple[Optional[int], Optional[Tracer]]:
    top, err = _validate_top(args.top)
    if err is not None:
        return err, None
    args.top = top

    ignore_patterns, err = _compile_ignore_patterns(args.ignore)
    if err is not None:
        return err, None

    tracer = Tracer(os.getcwd(), ignore_patterns=ignore_patterns)
    tracer.start()
    return None, tracer


def _finish_trace(tracer: Tracer, args: Namespace) -> Optional[int]:
    data = tracer.get_trace_data()
    _export_results(data, args)
    tracer.show_results(args.top)
    return _compare_and_fail(data, args)


def _run_target() -> int:
    parser: ArgumentParser = ArgumentParser(
        prog=_MODULE_NAME,
        description="OracleTrace - Lightweight execution tracer for Python projects",
        epilog="Subcommands:\n  run  Run a command (e.g., pytest) with tracing. See 'oracletrace run --help'.",
        parents=[_BASE_PARSER],
    )
    parser.add_argument("target", help="Python script to trace")
    parser.add_argument(
        "--version",
        action="version",
        help="Print version information then exit with a zero code",
        version=f"%(prog)s {version(_MODULE_NAME)}",
    )
    args: Namespace = parser.parse_args()

    target: str = args.target

    err, tracer = _init_tracer(args)
    if err is not None:
        return err
    assert tracer is not None

    if not os.path.exists(target):
        print(f"Target not found: {target}", file=sys.stderr)
        return 1

    target = os.path.abspath(target)
    target_dir: str = os.path.dirname(target)
    sys.path.insert(0, target_dir)

    try:
        runpy.run_path(target, run_name="__main__")
    finally:
        tracer.stop()

    exit_code = _finish_trace(tracer, args)
    return exit_code if exit_code is not None else 0


def _run_command(argv: List[str]) -> int:
    parser: ArgumentParser = ArgumentParser(
        prog=f"{_MODULE_NAME} run",
        description="Run a command with OracleTrace tracing",
        parents=[_BASE_PARSER],
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run (e.g., pytest). Use -- to separate oracletrace options from the command.",
    )

    parsed: Namespace = parser.parse_args(argv)

    if parsed.command and parsed.command[0] == "--":
        parsed.command = parsed.command[1:]

    if not parsed.command:
        print(
            "error: no command specified. "
            "Usage: oracletrace run [options] -- <command> [args...]",
            file=sys.stderr,
        )
        return 1

    cmd: str = parsed.command[0]

    if cmd == "pytest":
        return _run_pytest(parsed)
    else:
        print(
            f"error: unsupported command '{cmd}'. Only 'pytest' is supported.",
            file=sys.stderr,
        )
        return 1


def _run_pytest(args: Namespace) -> int:
    try:
        import pytest
    except ImportError:
        print(
            "error: pytest is not installed. Install it with: pip install pytest",
            file=sys.stderr,
        )
        return 1

    err, tracer = _init_tracer(args)
    if err is not None:
        return err
    assert tracer is not None

    try:
        pytest_exit_code: int = pytest.main(args.command[1:])
    finally:
        tracer.stop()

    exit_code = _finish_trace(tracer, args)
    return exit_code if exit_code is not None else pytest_exit_code


if __name__ == "__main__":
    sys.exit(main())
