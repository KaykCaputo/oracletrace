import re
import sys
import os
import json
import runpy
import csv
from collections import defaultdict

from .tracer import Tracer, TracerData, TracerMetadata, FunctionData
from .compare import compare_traces, ComparisonData
from typing import List, Dict, Optional
from re import Pattern
from argparse import ArgumentParser, Namespace
from dataclasses import asdict


def main() -> int:
    parser: ArgumentParser  = ArgumentParser(
        description="OracleTrace - Lightweight execution tracer for Python projects"
    )
    parser.add_argument("target", help="Python script to trace")
    parser.add_argument("--json", help="Export trace result to JSON file")
    parser.add_argument("--compare", help="Compare against previous trace JSON")
    parser.add_argument("--csv", help="Export trace result to CSV file")
    parser.add_argument(
        "--ignore",
        metavar="REGEX",
        nargs="+",
        help="Space separated list of regex patterns for keys (file path and function name) to ignore."
    )
    parser.add_argument(
        "--top",
        metavar="NUMBER",
        help="Limits the number of functions shown in the summary table"
    )
    parser.add_argument(
    "--fail-on-regression",
    action="store_true",
    help="Exit with a non-zero code when regression exceeds threshold.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="Regression threshold percentage used with --fail-on-regression.",
    )
    parser.add_argument(
        "--only-regressions",
        action="store_true",
        help="Hide functions which didn't run slower than baseline. Use with --compare"
    )

    parser.add_argument(
        "--repeat",
        metavar="NUMBER",
        help="Number of times to run the trace against the previous trace JSON",
        default=1
    )

    args: Namespace = parser.parse_args()

    target: str = args.target

    # Validate --top argument manually to ensure all paths are testable
    if args.top is not None:
        try:
            args.top = int(args.top)
        except ValueError:
            print(f"argument --top: invalid int value: '{args.top}'", file=sys.stderr)
            return 2
        if args.top < 1:
            print(f"--top must be a positive integer, got: {args.top}", file=sys.stderr)
            return 1

    if not os.path.exists(target):
        print(f"Target not found: {target}", file=sys.stderr)
        return 1

    target = os.path.abspath(target)
    root: str = os.getcwd()
    target_dir: str = os.path.dirname(target)
    # Setup paths so imports work correctly in the target script
    sys.path.insert(0, target_dir)
    ignored_args: List[str] = [] if args.ignore is None else args.ignore
    ignore_patterns: List[Pattern] = []

    for pattern in ignored_args:
        try:
            ignore_patterns.append(re.compile(pattern))
        except re.error as e:
            print(f"Regex error: {pattern} -> {e}", file=sys.stderr)
            return 1

    def run_trace():
        _tracer: Tracer = Tracer(root, ignore_patterns=ignore_patterns)

        _tracer.start()
        try:
            runpy.run_path(target, run_name="__main__")
        finally:
            _tracer.stop()

        _data: TracerData = _tracer.get_trace_data()

        return _tracer, _data

    tracer, data = run_trace()

    runs: int = int(args.repeat)
    if runs > 1:
        total_time: float = 0
        tracer_function_aggs: Dict[str, FunctionData] = {}
        for _ in range(runs):
            # Start tracing, run the script, then stop
            tracer, data = run_trace()

            for function_data in data.functions:
                if tracer_function_aggs.get(function_data.name) is None:
                    tracer_function_aggs[function_data.name] = function_data
                else:
                    tracer_function_aggs[function_data.name].add(function_data)
                total_time += function_data.total_time

        tracer_agg: TracerData = TracerData(
            metadata=TracerMetadata(
                root_path=data.metadata.root_path,
                total_functions=len(tracer_function_aggs),
                total_execution_time=total_time
            ),
            functions=list(tracer_function_aggs.values())
        )

        data = tracer_agg

    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError

    # Save json
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(asdict(data), f, indent=4, default=set_default)

    # Display the analysis
    if runs <= 1:
        if args.top:
            tracer.show_results(int(args.top))
        else:
            tracer.show_results(None)

    # Export as csv
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer: csv.DictWriter = csv.DictWriter(f, fieldnames=["function", "total_time", "calls", "avg_time"])
            writer.writeheader()
            for fn in data.functions:
                writer.writerow({
                    "function":   fn.name,
                    "total_time": fn.total_time,
                    "calls":      fn.call_count,
                    "avg_time":   fn.avg_time,
                })

    comparison_result: Optional[ComparisonData] = None

    # Compare jsons
    if args.compare:
        if not os.path.exists(args.compare):
            print(f"Compare file not found: {args.compare}", file=sys.stderr)
            return 1

        with open(args.compare, "r", encoding="utf-8") as f:
            old_data: TracerData = TracerData.from_dict(json.load(f))

        comparison_result = compare_traces(old_data, data, threshold=args.threshold, show_only_regressions=args.only_regressions)

        if args.fail_on_regression and comparison_result.has_regression:
            print(
                f"Build failed: performance regression above {args.threshold:.2f}% detected.",
                file=sys.stderr,
            )
            return 2


    return 0


if __name__ == "__main__":
    sys.exit(main())
