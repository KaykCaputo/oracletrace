# OracleTrace — Python Performance Profiler
> Detect performance regressions between runs in seconds — without heavy profilers.

<table><tr>
<td><img src="https://raw.githubusercontent.com/KaykCaputo/oracletrace/master/oracletracecat.png" alt="OracleTrace Logo"/></td>
<td>

**OracleTrace** is a lightweight Python tool that compares two execution traces and instantly shows what got slower, what changed, and what disappeared — so you catch regressions before they ship.

</td>
</tr></table>

[![PyPI](https://img.shields.io/pypi/v/oracletrace?label=PyPI)](https://pypi.org/project/oracletrace) [![PyPI Downloads](https://static.pepy.tech/personalized-badge/oracletrace?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/oracletrace)
[![GitHub Stars](https://img.shields.io/github/stars/KaykCaputo/oracletrace?style=social)](https://github.com/KaykCaputo/oracletrace/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/KaykCaputo/oracletrace?style=social)](https://github.com/KaykCaputo/oracletrace/network/members)

Documentation: https://kaykcaputo.github.io/oracletrace/

> 📰 Featured in [PyCoder's Weekly #729](https://pycoders.com/issues/729) · Listed in [awesome-debugger](https://github.com/taowen/awesome-debugger)

---

## Quick Regression Example

```bash
# Capture baseline
oracletrace app.py --json baseline.json

# After refactoring, compare against baseline
oracletrace app.py --json new.json --compare baseline.json
```

```
Performance Regression Detected

- calculate_results  → 2.1x slower  (0.20s → 0.42s)
+ new_cache_layer      detected (0.05s)
- old_helper           removed
```

---

### See OracleTrace in action:
![OracleTrace CLI demo](https://raw.githubusercontent.com/KaykCaputo/oracletrace/master/oracletrace-cli-demo.gif)

---

It is ideal for:

* Detecting performance regressions between script versions
* Comparing execution time across runs
* Visualizing function call graphs
* Lightweight profiling without heavy instrumentation
* CI performance validation

---

## How is this different?

| Tool        | Focus                          |
|-------------|--------------------------------|
| cProfile    | Deep profiling                 |
| viztracer   | Full execution tracing         |
| OracleTrace | Regression detection & diffing |

---

## Why OracleTrace?

Performance regressions in Python projects are often hard to detect early. Traditional profilers focus on deep analysis but are not optimized for quickly comparing two executions.

OracleTrace solves this by allowing you to:

* Run a script and generate an execution trace
* Export results to JSON
* Compare two trace files
* Identify performance differences
* Detect new or removed functions
* Measure execution time deltas

---

## Not Intended For

* Deep micro-optimization profiling (use cProfile or py-spy)
* Memory profiling (use memory_profiler or Memray)
* Production tracing or monitoring

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

---

## Contributors

Thanks to all the people who have contributed to this project:

<a href="https://github.com/KaykCaputo/oracletrace/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=KaykCaputo/oracletrace" />
</a>

---

## ⭐ Support the Project

If you find OracleTrace useful, give it a ⭐ on GitHub:

👉 https://github.com/KaykCaputo/oracletrace

Your support helps improve the project and makes it more visible to others.

---

Maintained by [Kayk Caputo](https://github.com/KaykCaputo) and [André Gustavo](https://github.com/AndreXP1)
