title: CLI Reference
description: Complete OracleTrace CLI reference with command syntax, options, workflows, and exit behavior.
keywords: oracletrace cli, oracle trace cli, python oracle trace cli, python trace command, --json option, --compare option, performance regression cli, execution trace command, call graph cli tool, command line profiler, terminal performance analysis, cat logo profiler, blackcat profiler
og_title: OracleTrace CLI Reference
og_description: Command syntax, options, workflows, and exit behavior for OracleTrace.

# CLI Reference

Complete command reference for OracleTrace.

## Command syntax

```bash
oracletrace <target> [--json OUTPUT.json] [--csv OUTPUT.csv] [--html OUTPUT.html] [--compare BASELINE.json]
oracletrace <target> [--ignore REGEX [REGEX ...]]
oracletrace <target> [--top NUMBER]
oracletrace <target> [--compare BASELINE.json] [--fail-on-regression] [--threshold PERCENT] [--only-regressions]
oracletrace --version
oracletrace run [options] -- pytest [pytest-args...]
```

## Tracing a Python script

### Required argument

#### `target`

Path to the Python script you want to trace.

Example:

```bash
oracletrace my_app.py
```

## Running a command with `oracletrace run`

The `run` subcommand lets you trace commands like `pytest` instead of a single script.

```bash
oracletrace run [options] -- pytest [pytest-args...]
```

All standard OracleTrace options (`--json`, `--csv`, `--html`, `--compare`, `--fail-on-regression`, `--threshold`, `--ignore`, `--top`) work with `run`. Use `--` to separate OracleTrace options from the command and its arguments.

Example:

```bash
oracletrace run --json trace.json -- pytest tests/ -x -v
```

### Behaviour

- OracleTrace starts tracing, then calls `pytest.main()` in-process with the provided arguments
- Trace data is captured across all user code exercised by the test suite
- If `--fail-on-regression` is set and a regression is detected, the exit code is `2` regardless of the pytest exit code
- If no regression is detected, the pytest exit code is propagated

## Optional arguments

### `--json`

Exports trace results to a JSON file.

```bash
oracletrace my_app.py --json run.json
```

Use this when you want to keep historical traces or compare later.

### `--csv`

Exports the trace results to a csv file.

```bash
oracletrace my_app.py --csv run.csv
```

### `--html`

Exports the trace results to an interactive HTML file.

```bash
oracletrace my_app.py --html report.html
```

The generated report includes a sortable table with function timing data and a call graph visualization.

### `--compare`

Compares the current run against a previous JSON trace.

```bash
oracletrace my_app.py --json current.json --compare baseline.json
```

Comparison output includes:

- Functions with performance increase or decrease
- Newly added functions
- Removed functions

### `--fail-on-regression`

Makes OracleTrace return a non-zero exit code when a regression exceeds the configured threshold.

Use this together with `--compare`.

Example:

```bash
oracletrace my_app.py --json current.json --compare baseline.json --fail-on-regression --threshold 25
```

### `--threshold`

Sets the percentage threshold used with `--fail-on-regression`.

Default value: `5.0`

```bash
oracletrace my_app.py --compare baseline.json --fail-on-regression --threshold 25
```

### `---only-regressions`

Shows only the regressions in the diff output when comparing traces.

Use with `--compare`.

Default value: False

```bash
oracletrace my_app.py --compare baseline.json --only-regressions
```

### `--ignore`

Specify file paths and function names to ignore using regular expression syntax.

```bash
oracletrace my_app.py --ignore ".*test.*" ".*helpers.py:debug_.*"
```

The ignored files and functions will not appear in the summary table neither the logic flow output.

Ignore matching is applied on function keys in the form `relative_path.py:qualified_function_name`.

### `--top`

Limit the summary table output to a maximum number of results.

```bash
oracletrace my_app.py --top 10
```

### `--version`

Prints version information and exit with a zero code.

```bash
oracletrace --version
```

## Exit behavior

| Exit code | Meaning |
|-----------|---------|
| `0` | Success |
| `1` | OracleTrace error (invalid arguments, missing files, etc.) **or** traced command error (e.g. pytest failures) when no regression is detected |
| `2` | Performance regression detected (`--fail-on-regression`) |

When `--fail-on-regression` finds a regression, exit code `2` takes priority over the traced command's exit code. Otherwise the traced command's exit code is propagated.

## Typical workflows

### Local development workflow

```bash
oracletrace app.py --json baseline.json
# change code
oracletrace app.py --json current.json --compare baseline.json
```

### CI regression workflow

```bash
oracletrace app.py --json current.json --compare baseline.json --fail-on-regression --threshold 10
```

Store `baseline.json` as a known-good artifact.

### CI regression workflow with pytest

```bash
# Generate baseline from a stable branch
oracletrace run --json baseline.json -- pytest tests/ -q

# Compare in a PR pipeline
oracletrace run --json current.json --compare baseline.json --fail-on-regression --threshold 25 -- pytest tests/ -q
```

This enables OracleTrace to act as a performance guardrail in test pipelines without modifying test code.

## Tips

- Run from your project root so filtering focuses on your app code
- Keep baseline and current runs as similar as possible
- Use deterministic input data for reliable comparisons
