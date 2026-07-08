import os
import re
import sys
import csv
import json
import runpy
import argparse
from re import Pattern
from statistics import median
from dataclasses import asdict
from importlib.metadata import version
from argparse import ArgumentParser, Namespace
from typing import List, Dict, Any, Optional, Tuple

from .reporters import generate_html_report
from .compare import compare_traces, ComparisonData
from .tracer import Tracer, TracerData, TracerMetadata, FunctionData, FunctionAggregate


_MODULE_NAME: str = __name__.split(".")[0]


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "run":
        return _run_command(sys.argv[2:])
    if len(sys.argv) >= 2 and sys.argv[1] == "baseline":
        return _run_baseline_command(sys.argv[2:])
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


def _validate_repeat(repeat_str: Any) -> Tuple[int, Optional[int]]:
    try:
        repeat = int(repeat_str)
        if repeat < 1:
            raise ValueError
    except ValueError:
        print(f"argument --repeat: invalid int value: '{repeat_str}'", file=sys.stderr)
        return 0, 1
    return repeat, None


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
_BASE_PARSER.add_argument(
    "--repeat",
    metavar="NUMBER",
    help="Number of times to repeat the trace run and aggregate results",
    default=1,
)

_BASELINE_SAVE_PARSER: ArgumentParser = ArgumentParser(add_help=False)
_BASELINE_SAVE_PARSER.add_argument("--csv", help="Export trace result to CSV file")
_BASELINE_SAVE_PARSER.add_argument("--html", help="Export trace result to interactive HTML file")
_BASELINE_SAVE_PARSER.add_argument(
    "--ignore",
    metavar="REGEX",
    nargs="+",
    help="Space separated list of regex patterns for keys (file path and function name) to ignore.",
)
_BASELINE_SAVE_PARSER.add_argument(
    "--top",
    metavar="NUMBER",
    help="Limits the number of functions shown in the summary table",
)
_BASELINE_SAVE_PARSER.add_argument(
    "--repeat",
    metavar="NUMBER",
    help="Number of times to repeat the trace run and aggregate results",
    default=1,
)


def _set_default(obj: Any) -> Any:
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


def _export_results(data: TracerData, args: Namespace) -> None:
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(asdict(data), f, indent=4, default=_set_default)

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


def _compare_files(args: Namespace) -> int:
    if not os.path.exists(args.baseline):
        print(f"Baseline file not found: {args.baseline}", file=sys.stderr)
        return 1

    if not os.path.exists(args.current):
        print(f"Current trace file not found: {args.current}", file=sys.stderr)
        return 1

    with open(args.baseline, "r", encoding="utf-8") as f:
        baseline_data: TracerData = TracerData.from_dict(json.load(f))

    with open(args.current, "r", encoding="utf-8") as f:
        current_data: TracerData = TracerData.from_dict(json.load(f))

    comparison_result: ComparisonData = compare_traces(
        baseline_data,
        current_data,
        threshold=args.threshold,
        show_only_regressions=args.only_regressions,
    )

    if args.fail_on_regression and comparison_result.has_regression:
        print(
            f"Build failed: performance regression above {args.threshold:.2f}% detected.",
            file=sys.stderr,
        )
        return 2

    return 0


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


def _trace_script(target: str, args: Namespace) -> Tuple[Optional[int], Optional[TracerData], Optional[Tracer]]:
    top, err = _validate_top(args.top)
    if err is not None:
        return err, None, None
    args.top = top

    repeat, err = _validate_repeat(args.repeat)
    if err is not None:
        return err, None, None
    args.repeat = repeat

    ignore_patterns, err = _compile_ignore_patterns(args.ignore)
    if err is not None:
        return err, None, None

    if not os.path.exists(target):
        print(f"Target not found: {target}", file=sys.stderr)
        return 1, None, None

    target = os.path.abspath(target)
    target_dir: str = os.path.dirname(target)
    sys.path.insert(0, target_dir)

    root: str = os.getcwd()

    def run_trace() -> Tuple[Tracer, TracerData]:
        _tracer: Tracer = Tracer(root, ignore_patterns=ignore_patterns)
        _tracer.start()
        try:
            runpy.run_path(target, run_name="__main__")
        finally:
            _tracer.stop()
        return _tracer, _tracer.get_trace_data()

    runs: int = args.repeat

    if runs > 1:
        aggs: Dict[str, FunctionAggregate] = {}
        wall_times: List[float] = []
        data: TracerData

        for _ in range(runs):
            _, data = run_trace()
            wall_times.append(data.metadata.total_execution_time)
            for function_data in data.functions:
                if function_data.name not in aggs:
                    aggs[function_data.name] = FunctionAggregate(name=function_data.name)
                aggs[function_data.name].add(function_data)

        data = TracerData(
            metadata=TracerMetadata(
                root_path=data.metadata.root_path,
                total_functions=len(aggs),
                total_execution_time=median(wall_times),
            ),
            functions=[agg.to_function_data() for agg in aggs.values()],
        )
        return None, data, None

    tracer, data = run_trace()
    return None, data, tracer


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

    err, data, tracer = _trace_script(args.target, args)
    if err is not None:
        return err

    assert data is not None
    if tracer is None:
        _export_results(data, args)
        exit_code = _compare_and_fail(data, args)
        return exit_code if exit_code is not None else 0

    exit_code = _finish_trace(tracer, args)
    return exit_code if exit_code is not None else 0


def _run_baseline_command(argv: List[str]) -> int:
    parser: ArgumentParser = ArgumentParser(
        prog=f"{_MODULE_NAME} baseline",
        description="Create and compare OracleTrace baseline files",
    )
    subparsers = parser.add_subparsers(dest="baseline_command", required=True)

    save_parser = subparsers.add_parser(
        "save",
        parents=[_BASELINE_SAVE_PARSER],
        help="Trace a Python script and save the result as a baseline JSON file",
    )
    save_parser.add_argument("target", help="Python script to trace")
    save_parser.add_argument("output", help="Baseline JSON file to write")

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare two saved OracleTrace JSON files",
    )
    compare_parser.add_argument("baseline", help="Baseline JSON file")
    compare_parser.add_argument("current", help="Current trace JSON file")
    compare_parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with a non-zero code when regression exceeds threshold.",
    )
    compare_parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="Regression threshold percentage used with --fail-on-regression.",
    )
    compare_parser.add_argument(
        "--only-regressions",
        action="store_true",
        help="Hide functions which didn't run slower than baseline.",
    )

    args: Namespace = parser.parse_args(argv)

    if args.baseline_command == "compare":
        return _compare_files(args)

    args.json = args.output
    err, data, tracer = _trace_script(args.target, args)
    if err is not None:
        return err

    assert data is not None
    _export_results(data, args)
    print(f"Baseline saved: {os.path.abspath(args.output)}")
    if tracer is not None:
        tracer.show_results(args.top)
    return 0


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
