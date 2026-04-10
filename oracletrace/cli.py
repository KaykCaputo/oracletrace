import re
import sys
import os
import json
import runpy
import csv
from .tracer import Tracer, TracerData
from .compare import compare_traces, ComparisonData
from typing import List, Dict, Any, Optional
from re import Pattern
from argparse import ArgumentParser, Namespace
from pathlib import Path
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
    args: Namespace = parser.parse_args()

    target: str = args.target

    if not os.path.exists(target):
        print(f"Target not found: {target}")
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
            print(f"Regex error: {pattern} -> {e}")
            return 1

    # Start tracing, run the script, then stop
    tracer: Tracer = Tracer(root, ignore_patterns=ignore_patterns)
    tracer.start()
    try:
        runpy.run_path(target, run_name="__main__")
    finally:
        tracer.stop()

    data: TracerData = tracer.get_trace_data()

    # Save json
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(asdict(data), f, indent=4)

    # Display the analysis
    if args.top:
        tracer.show_results(int(args.top[0]))
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
            print(f"Compare file not found: {args.compare}")
            return 1

        with open(args.compare, "r", encoding="utf-8") as f:
            old_data: TracerData = TracerData.from_dict(json.load(f))

        comparison_result = compare_traces(old_data, data, threshold=args.threshold)

        if args.fail_on_regression and comparison_result.has_regression:
            print(
            f"Build failed: performance regression above {args.threshold:.2f}% detected."
            )
            return 2
        

    return 0


if __name__ == "__main__":
    sys.exit(main())
