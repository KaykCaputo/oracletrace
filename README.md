# OracleTrace

**OracleTrace** is a simple logic path tracer for Python applications. It visualizes the execution flow of your code, helping you understand function calls and performance bottlenecks.

- **PyPI:** https://pypi.org/project/oracletrace/
- **GitHub:** https://github.com/KaykCaputo/oracletrace

## Installation

```bash
pip install oracletrace
```

## Usage

Run `oracletrace` on your Python script:

```bash
oracletrace your_script.py
```

Or run it as a module:

```bash
python -m oracletrace.cli your_script.py
```

## Features

- **Logic Flow Visualization**: See a tree structure of function calls.
- **Performance Metrics**: View execution time and call counts for each function.
- **Clean Output**: Filters out internal Python calls for better readability.

## Requirements

- Python >= 3.10
- [rich](https://github.com/Textualize/rich)
