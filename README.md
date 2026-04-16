# OracleTrace — Detect Python Performance Regressions with Execution Diff

> Detect performance regressions between runs of your Python script in seconds.

<table><tr>
<td><img src="https://raw.githubusercontent.com/KaykCaputo/oracletrace/master/oracletracecat.png" alt="OracleTrace Logo" width="185"/></td>
<td>

**Run your script twice. See exactly what got slower.**

OracleTrace works like a **git diff for performance**.

</td>
</tr></table>

[![PyPI](https://img.shields.io/pypi/v/oracletrace?label=PyPI)](https://pypi.org/project/oracletrace)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/oracletrace?period=total\&units=INTERNATIONAL_SYSTEM\&left_color=BLACK\&right_color=GREEN\&left_text=downloads)](https://pepy.tech/projects/oracletrace)
[![GitHub Stars](https://img.shields.io/github/stars/KaykCaputo/oracletrace?style=social)](https://github.com/KaykCaputo/oracletrace/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/KaykCaputo/oracletrace?style=social)](https://github.com/KaykCaputo/oracletrace/network/members)
[![CI Tests](https://github.com/KaykCaputo/oracletrace/actions/workflows/tests.yml/badge.svg)](https://github.com/KaykCaputo/oracletrace/actions/workflows/tests.yml)

Documentation: [https://kaykcaputo.github.io/oracletrace/](https://kaykcaputo.github.io/oracletrace/)

**Featured in:** [PyCoder's Weekly #729](https://pycoders.com/issues/729) • [awesome-debugger](https://github.com/taowen/awesome-debugger) • [awesome-profiling](https://github.com/msaroufim/awesome-profiling)

---
### Installation
```bash
pip install oracletrace
```

## Quick Start

### 1. See where your program spends time instantly:
```bash
oracletrace app.py
```

### 2. Compare runs and detect regressions:
```bash
oracletrace app.py --json baseline.json
oracletrace app.py --json new.json --compare baseline.json
```

---

## See it in action

See exactly which functions got slower between runs:

![OracleTrace CLI demo](https://raw.githubusercontent.com/KaykCaputo/oracletrace/master/oracletrace-cli-demo.gif)

---

## Example Output

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

## Why OracleTrace?

### Problem

Performance regressions are hard to detect early.

### Solution

OracleTrace compares execution traces and highlights what got slower.

### How it works

1. Run your script
2. Generate a trace
3. Compare results
4. Identify slowdowns

---

## CI Integration

Fail your pipeline when performance degrades:

```bash
oracletrace app.py --json current.json --compare baseline.json --fail-on-regression --threshold 25
```
Add it to your CI to automatically fail on performance regressions.

---

## Key Features

* Detect slower and faster functions
* Identify new or removed functions
* Execution time and call count analysis
* Call graph visualization
* JSON and CSV export
* Regex-based filtering (`--ignore`)
* Top-N function focus (`--top`)
* CI regression gates

---

## CLI Reference

| Flag                   | Description                            |
| ---------------------- | -------------------------------------- |
| `--json`               | Export trace to JSON                   |
| `--csv`               | Export trace to CSV                     |
| `--compare`            | Compare with another trace             |
| `--fail-on-regression` | Exit with error if regression detected |
| `--threshold`          | Regression percentage threshold        |
| `--ignore`             | Ignore functions/files via regex       |
| `--top`                | Show top N functions                   |

---

## Use Cases

### Primary

* Detect performance regressions between runs

### Secondary

* CI performance validation
* Execution trace inspection
* Call graph visualization

---

## How It Works

OracleTrace uses Python’s `sys.setprofile()` to intercept function calls and returns.

It measures execution time per function and records caller–callee relationships.

Filtering removes external/internal calls to focus on application code.

---

## Requirements

* Python >= 3.10
* rich

---

## Contributing

Contributions are welcome.

Please read the [Contributing Guide](CONTRIBUTING.md) for details on how to get started, coding standards, and the contribution process.

---

## Contributors

<a href="https://github.com/KaykCaputo/oracletrace/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=KaykCaputo/oracletrace" />
</a>

---

## ⭐ Support the Project

If OracleTrace is useful, consider giving it a star:

[GitHub Repository](https://github.com/KaykCaputo/oracletrace)

---

## Maintainers

* [Kayk Caputo](https://github.com/KaykCaputo)
* [André Gustavo](https://github.com/AndreXP1)
