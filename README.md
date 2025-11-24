# OracleTrace

**OracleTrace** is a simple logic path tracer for Python applications. It visualizes the execution flow of your code, helping you understand function calls and performance bottlenecks.

- **PyPI:** https://pypi.org/project/oracletrace/
- **GitHub:** https://github.com/KaykCaputo/oracletrace



## Features
- **Performance Summary Table:** Visualize the most time-consuming functions with a clean table showing totam time, and average time per call.
- **Logic Flow Visualization**: See a tree structure of function calls.
- **Performance Metrics**: View execution time and call counts for each function.
- **Clean Output**: Filters out internal Python calls for better readability.

## How It Works

OracleTrace uses Python's built-in `sys.setprofile()` function to intercept function call events (`call`, `return`). It measures the time spent inside each function and records the caller-callee relationships. By tracking the file path of each function, it can filter out calls that are not part of your local project directory, resulting in a clean and relevant report.


## Installation

```bash
pip install oracletrace
```

## Quick Start

1.  **Create a Python script.** For example, save the following as `my_app.py`:

    ```python
    # my_app.py
    import time

    def process_data():
        print("  > Processing data...")
        time.sleep(0.1)
        calculate_results()

    def calculate_results():
        print("    > Calculating results...")
        time.sleep(0.2)

    def main():
        print("Starting application...")
        for i in range(2):
            print(f"\nIteration {i+1}:")
            process_data()
        print("\nApplication finished.")

    if __name__ == "__main__":
        main()
    ```

2.  **Run `oracletrace` from your terminal:**

    ```bash
    oracletrace your_script.py
    ```

    Or run it as a module:

    ```bash
    python -m oracletrace.cli your_script.py
    ```

## Example Output

Running the command above will execute your script and then generate a report like this:

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


## Requirements

- Python >= 3.10
- [rich](https://github.com/Textualize/rich)
