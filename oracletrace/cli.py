import sys
import os
import json
import argparse
import runpy
from .tracer import Tracer
from .compare import compare_traces


def main():
    parser = argparse.ArgumentParser(
        description="OracleTrace - Lightweight execution tracer for Python projects"
    )
    parser.add_argument("target", help="Python script to trace")
    parser.add_argument("--json", help="Export trace result to JSON file")
    parser.add_argument("--compare", help="Compare against previous trace JSON")
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

    # Start tracing, run the script, then stop
    tracer = Tracer(root)
    tracer.start()
    try:
        runpy.run_path(target, run_name="__main__")
    finally:
        tracer.stop()

    data = tracer.get_trace_data()

    # Save json
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # Display the analysis
    tracer.show_results()

    # Compare jsons
    if args.compare:
        if not os.path.exists(args.compare):
            print(f"Compare file not found: {args.compare}")
            return 1

        with open(args.compare, "r", encoding="utf-8") as f:
            old_data = json.load(f)

        compare_traces(old_data, data)

    return 0


if __name__ == "__main__":
    sys.exit(main())
