title: Quickstart
description: Learn OracleTrace quickly: trace a Python script, save a baseline JSON, and compare runs to detect performance regressions.
keywords: oracletrace quickstart, oracle trace quickstart, python oracle trace quickstart, python performance regression, compare execution traces, baseline json, call graph quickstart, trace profiler tutorial, script performance check, regression detection tutorial, cat logo profiler, blackcat profiler
og_title: OracleTrace Quickstart
og_description: Trace a Python script, save a baseline JSON, and compare runs to detect performance regressions.

# Quickstart

This quickstart shows how to trace a script, create a baseline, and detect a performance regression.

## 1. Create a sample script

Create a file named `my_app.py`:

```python
import time


def process_data():
    time.sleep(0.10)
    calculate_results()


def calculate_results():
    time.sleep(0.20)


def main():
    for _ in range(2):
        process_data()


if __name__ == "__main__":
    main()
```

## 2. Run a trace

```bash
oracletrace my_app.py
```

![OracleTrace CLI demo](assets/oracletrace-cli-demo.gif)

You will see:

- Top functions by total time
- Call counts and average time per call
- Call graph logic flow

## 3. Save a baseline trace

```bash
oracletrace my_app.py --json baseline.json
```

Keep this file as your reference run.

## 4. Simulate a regression and compare

Increase one of the `sleep` values in your script, then run:

```bash
oracletrace my_app.py --json new.json --compare baseline.json
```

Comparison output highlights:

- Functions that got slower
- Functions that got faster
- Newly added or removed functions

## 5. Understand the output quickly

Example flow:

```text
<module>
└── my_app.py:main
    └── my_app.py:process_data
        └── my_app.py:calculate_results
```

OracleTrace is optimized for relative change detection between runs, which makes it ideal for everyday checks and CI validation.