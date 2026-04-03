title: CLI Reference
description: Complete OracleTrace CLI reference with command syntax, options, workflows, and exit behavior.
keywords: oracletrace cli, oracle trace cli, python oracle trace cli, python trace command, --json option, --compare option, performance regression cli, execution trace command, call graph cli tool, command line profiler, terminal performance analysis, cat logo profiler, blackcat profiler
og_title: OracleTrace CLI Reference
og_description: Command syntax, options, workflows, and exit behavior for OracleTrace.

# CLI Reference

Complete command reference for OracleTrace.

## Command syntax

```bash
oracletrace <target> [--json OUTPUT.json] [--csv OUTPUT.csv] [--compare BASELINE.json]
oracletrace <target> [--ignore REGEX [REGEX ...]]
oracletrace <target> [--top NUMBER]
oracletrace <target> [--compare BASELINE.json] [--fail-on-regression] [--threshold PERCENT]
```

## Required argument

### `target`

Path to the Python script you want to trace.

Example:

```bash
oracletrace my_app.py
```

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

Example:

```bash
oracletrace my_app.py --json current.json --compare baseline.json --fail-on-regression --threshold 25
```

### `--threshold`

Sets the percentage threshold used with `--fail-on-regression`.

```bash
oracletrace my_app.py --compare baseline.json --fail-on-regression --threshold 25
```

### `--ignore`

Specify file paths and function names to ignore using regular expression syntax.

```bash
oracletrace my_app.py --ignore *test* *test*.py
```

The ignored files and functions will not appear in the summary table neither the logic flow output.

### `--top`

Limit the summary table output to a maximum number of results.

```bash
oracletrace my_app.py --top 10
```

## Exit behavior

OracleTrace returns a non-zero exit code when:

- The target script does not exist
- The compare JSON file does not exist
- `--fail-on-regression` is enabled and at least one function regresses above the threshold

Non-zero exit codes can also happen when the target script fails at runtime or when the compare JSON file cannot be parsed.

## Typical workflows

### Local development workflow

```bash
oracletrace app.py --json baseline.json
# change code
oracletrace app.py --json current.json --compare baseline.json
```

### CI regression workflow

```bash
oracletrace app.py --json current.json --compare baseline.json
```

Store `baseline.json` as a known-good artifact.

## Tips

- Run from your project root so filtering focuses on your app code
- Keep baseline and current runs as similar as possible
- Use deterministic input data for reliable comparisons
