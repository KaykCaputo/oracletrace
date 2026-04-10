# OracleTrace — Python Performance Profiler
> Detect Python performance regressions and compare execution traces with a lightweight call graph profiler.
<table><tr>
<td><img src="https://raw.githubusercontent.com/KaykCaputo/oracletrace/master/oracletracecat.png" alt="OracleTrace Logo"/></td>
<td>

**OracleTrace** is a lightweight Python performance analysis tool designed to help developers detect performance regressions, compare execution traces, and visualize call graphs in a simple and readable way.

</td>
</tr></table>

It is ideal for:

* Detecting performance regressions between script versions
* Comparing execution time across runs
* Visualizing function call graphs
* Lightweight profiling without heavy instrumentation
* CI performance validation

[![PyPI](https://img.shields.io/pypi/v/oracletrace?label=PyPI)](https://pypi.org/project/oracletrace) [![PyPI Downloads](https://static.pepy.tech/personalized-badge/oracletrace?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/oracletrace)
[![GitHub Stars](https://img.shields.io/github/stars/KaykCaputo/oracletrace?style=social)](https://github.com/KaykCaputo/oracletrace/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/KaykCaputo/oracletrace?style=social)](https://github.com/KaykCaputo/oracletrace/network/members)
[![CI Tests](https://github.com/KaykCaputo/oracletrace/actions/workflows/tests.yml/badge.svg)](https://github.com/KaykCaputo/oracletrace/actions/workflows/tests.yml)


Documentation: https://kaykcaputo.github.io/oracletrace/

---
### See OracleTrace in action:
![OracleTrace CLI demo](https://raw.githubusercontent.com/KaykCaputo/oracletrace/master/oracletrace-cli-demo.gif)
---
## Why OracleTrace?

Performance regressions in Python projects are often hard to detect early.

Traditional profilers focus on deep performance analysis, but they are not optimized for quick regression comparison between two executions.

OracleTrace solves this by allowing you to:

* Run a script and generate an execution trace
* Export results to JSON
* Compare two trace files
* Identify performance differences
* Detect new or removed functions
* Measure execution time deltas

---

## Key Features

### Performance Regression Detection

Compare two JSON trace files and instantly see:

* Slower functions
* Faster functions
* New functions
* Removed functions

### Execution Trace Analysis

* Total execution time per function
* Average time per call
* Call counts
* Caller → callee relationships

### Call Graph Visualization

Visual tree structure of your program’s execution flow.

### JSON Export

Export trace results for:

* CI performance checks
* Historical comparison
* Automation pipelines

### CSV Export

Export flat trace metrics for spreadsheets and custom reports.

### Flexible Filtering and Focus

* Ignore functions and files with regex patterns (`--ignore`)
* Limit summary output to top N functions (`--top`)

### CI Regression Gates

Use `--fail-on-regression` with `--threshold` to make pipelines fail on meaningful slowdowns.

### Clean Output

Filters internal Python calls to focus only on your project code.

---

## Installation

```bash
pip install oracletrace
```

---

## Quick Example

### Step 1 — Create a script

```python
import time

def process_data():
    time.sleep(0.1)
    calculate_results()

def calculate_results():
    time.sleep(0.2)

def main():
    for _ in range(2):
        process_data()

if __name__ == "__main__":
    main()
```

### Step 2 — Run OracleTrace

```bash
oracletrace my_app.py
```

### Export trace to JSON

```bash
oracletrace my_app.py --json baseline.json
```

### Compare with a new version

```bash
oracletrace my_app.py --json new.json --compare baseline.json
```

This allows you to detect performance regressions between two executions.

### Fail CI when regression exceeds threshold

```bash
oracletrace my_app.py --json current.json --compare baseline.json --fail-on-regression --threshold 25
```

---

## How It Works

OracleTrace uses Python’s built-in `sys.setprofile()` function to intercept:

* `call`
* `return`

It measures execution time per function and records caller-callee relationships.

By filtering functions outside your project directory, the output focuses only on relevant application code.

---

## Example Output

Summary table showing top functions by total execution time and average time per call.

Call graph visualization displaying execution flow hierarchy.

```
Starting application...

Iteration 1:
  > Processing data...
    > Calculating results...

Iteration 2:
  > Processing data...
    > Calculating results...

Application finished.

Summary:
                         Top functions by Total Time
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Function                     ┃ Total Time (s) ┃ Calls ┃ Avg. Time/Call (ms) ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ my_app.py:main               │         0.6025 │     1 │             602.510 │
│ my_app.py:process_data       │         0.6021 │     2 │             301.050 │
│ my_app.py:calculate_results  │         0.4015 │     2 │             200.750 │
└──────────────────────────────┴────────────────┴───────┴─────────────────────┘


Logic Flow:
<module>
└── my_app.py:main (1x, 0.6025s)
    └── my_app.py:process_data (2x, 0.6021s)
        └── my_app.py:calculate_results (2x, 0.4015s)
```

---

## Use Cases

* Detect Python performance regressions in development
* Compare execution time between versions
* Lightweight alternative to heavy profilers
* CI/CD performance monitoring
* Educational demonstration of call graphs

---

## Requirements

* Python >= 3.10
* rich

---

## Contributing

Contributions are welcome.

If you have ideas for improving regression detection, trace comparison, or visualization features, feel free to open an issue or submit a pull request.

To run tests locally:

```bash
pytest tests/
```

---

## Contributors

Thanks to all the people who have contributed to this project:

<a href="https://github.com/KaykCaputo/oracletrace/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=KaykCaputo/oracletrace" />
</a>

---

## Recognition

- Included in [awesome-debugger](https://github.com/taowen/awesome-debugger)
- Featured in [PyCoder's Weekly #729](https://pycoders.com/issues/729)

---

## ⭐ Support the Project

If you find OracleTrace useful, give it a ⭐ on GitHub:

👉 https://github.com/KaykCaputo/oracletrace

Your support helps improve the project and makes it more visible to others.

---

Maintained by [Kayk Caputo](https://github.com/KaykCaputo) and [André Gustavo](https://github.com/AndreXP1)
