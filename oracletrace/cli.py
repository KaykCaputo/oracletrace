import re
import sys
import os
import json
import argparse
import runpy
import csv
from collections import defaultdict
from .tracer import Tracer
from .compare import compare_traces


def _aggregate_trace_data(all_runs_data):
    """Aggregate trace data from multiple runs.

    Args:
        all_runs_data: List of trace data dicts from multiple runs.

    Returns:
        A single aggregated trace data dict.
    """
    # Aggregate function times and calls across all runs
    agg_func_time = defaultdict(float)
    agg_func_calls = defaultdict(int)
    agg_call_map = defaultdict(lambda: defaultdict(int))
    total_execution_time = 0.0

    for run_data in all_runs_data:
        total_execution_time += run_data["metadata"]["total_execution_time"]
        for fn in run_data["functions"]:
            key = fn["name"]
            agg_func_time[key] += fn["total_time"]
            agg_func_calls[key] += fn["call_count"]
            for callee_key, count in fn.get("callees", {}).items():
                agg_call_map[key][callee_key] += count

    # Build aggregated functions list
    functions = []
    for key in agg_func_time:
        total_time = agg_func_time[key]
        calls = agg_func_calls[key]
        avg_time = total_time / calls if calls else 0
        functions.append({
            "name": key,
            "total_time": total_time,
            "call_count": calls,
            "avg_time": avg_time,
            "callees": dict(agg_call_map.get(key, {})),
        })

    return {
        "metadata": {
            "root_path": all_runs_data[0]["metadata"]["root_path"],
            "total_functions": len(functions),
            "total_execution_time": total_execution_time,
            "runs": len(all_runs_data),
        },
        "functions": functions,
    }


def main():
    parser = argparse.ArgumentParser(
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
        "--repeat",
        metavar="N",
        type=int,
        default=1,
        help="Run the target script N times and aggregate the results (default: 1)"
    )
    args = parser.parse_args()

    target = args.target

    if not os.path.exists(target):
        print(f"Target not found: {target}")
        return 1

    target = os.path.abspath(target)
    root = os.getcwd()
    target_dir = os.path.dirname(target)
    # Setup paths so imports work correctly in the target script
    sys.path.insert(0, target_dir)
    ignored_args = [] if args.ignore is None else args.ignore
    ignore_patterns = []

    for pattern in ignored_args:
        try:
            ignore_patterns.append(re.compile(pattern))
        except re.error as e:
            print(f"Regex error: {pattern} -> {e}")
            return 1

    repeat = max(1, args.repeat)
    all_runs_data = []

    for i in range(repeat):
        if repeat > 1:
            print(f"[bold cyan]Run {i+1}/{repeat}[/]")

        # Start tracing, run the script, then stop
        tracer = Tracer(root, ignore_patterns=ignore_patterns)
        tracer.start()
        try:
            runpy.run_path(target, run_name="__main__")
        finally:
            tracer.stop()

        data = tracer.get_trace_data()
        all_runs_data.append(data)

    # Aggregate results if repeat > 1
    if repeat > 1:
        data = _aggregate_trace_data(all_runs_data)
        print(f"\n[bold green]Aggregated results from {repeat} runs:[/]")

    # Save json
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # Display the analysis
    if args.top:
        _show_aggregated_results(int(args.top[0]), data)
    else:
        _show_aggregated_results(None, data)

    # Export as csv
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["function", "total_time", "calls", "avg_time"])
            writer.writeheader()
            for fn in data["functions"]:
                writer.writerow({
                    "function":   fn["name"],
                    "total_time": fn["total_time"],
                    "calls":      fn["call_count"],
                    "avg_time":   fn["avg_time"],
                })


    # Compare jsons
    if args.compare:
        if not os.path.exists(args.compare):
            print(f"Compare file not found: {args.compare}")
            return 1

        with open(args.compare, "r", encoding="utf-8") as f:
            old_data = json.load(f)

        compare_traces(old_data, data)

    return 0


def _show_aggregated_results(_top, data):
    """Show aggregated results using the data structure.

    Mirrors the output format of Tracer.show_results() but works
    with the aggregated data dict directly.
    """
    from rich.tree import Tree
    from rich.table import Table
    from rich import print

    functions = data["functions"]
    if not functions:
        print("[yellow]No calls traced.[/]")
        return

    # Build lookup maps from data
    func_time = {fn["name"]: fn["total_time"] for fn in functions}
    func_calls = {fn["name"]: fn["call_count"] for fn in functions}
    call_map = {fn["name"]: fn.get("callees", {}) for fn in functions}

    total_time = data["metadata"]["total_execution_time"]

    # Summary table
    print("[bold green]Summary:[/]")
    print(f"[bold cyan]Total execution time: {total_time:.4f}s[/]")
    table = Table(title="Top functions by Total Time")
    table.add_column("Function", justify="left", style="cyan", no_wrap=True)
    table.add_column("Total Time (s)", justify="right", style="magenta")
    table.add_column("Calls", justify="right", style="green")
    table.add_column("Avg. Time/Call (ms)", justify="right", style="yellow")

    # sort functions by time
    _sorted_by_time = sorted(
        func_time.items(), key=lambda item: item[1], reverse=True
    )

    for key, fn_total_time in _sorted_by_time[:_top]:
        calls = func_calls[key]
        avg_time_ms = (fn_total_time / calls) * 1000 if calls > 0 else 0
        table.add_row(key, f"{fn_total_time:.4f}", str(calls), f"{avg_time_ms:.3f}")

    print(table)

    print("\n[bold green]Logic Flow:[/]")

    tree = Tree("[bold yellow]<module>[/]")

    # Recursively build the execution tree
    def add_nodes(parent_node, parent_key, current_path):
        children = call_map.get(parent_key, {})
        # Sort children by total execution time
        sorted_children = sorted(
            children.items(),
            key=lambda x: func_time.get(x[0], 0),
            reverse=True,
        )

        for child_key, count in sorted_children:
            fn_total_time = func_time.get(child_key, 0)
            # Detect recursion to prevent infinite loops in the tree
            if child_key in current_path:
                parent_node.add(f"[red]↻ {child_key}[/] ({count}x)")
                continue

            node_text = f"{child_key} [dim]({count}x, {fn_total_time:.4f}s)[/]"
            child_node = parent_node.add(node_text)
            add_nodes(child_node, child_key, current_path | {child_key})

    add_nodes(tree, "<module>", {"<module>"})
    print(tree)


if __name__ == "__main__":
    sys.exit(main())
