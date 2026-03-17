title: CLI Reference
description: Complete OracleTrace CLI reference with command syntax, options, workflows, and exit behavior.
keywords: oracletrace cli, oracle trace cli, python oracle trace cli, python trace command, --json option, --compare option, performance regression cli, execution trace command, call graph cli tool, command line profiler, terminal performance analysis, cat logo profiler, blackcat profiler
og_title: OracleTrace CLI Reference
og_description: Command syntax, options, workflows, and exit behavior for OracleTrace.

# CLI Reference

Complete command reference for OracleTrace.

## Command syntax

```bash
oracletrace <target> [--json OUTPUT.json] [--compare BASELINE.json]
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

### `--compare`

Compares the current run against a previous JSON trace.

```bash
oracletrace my_app.py --json current.json --compare baseline.json
```

Comparison output includes:

- Functions with performance increase or decrease
- Newly added functions
- Removed functions

## Exit behavior

OracleTrace returns a non-zero exit code when:

- The target script does not exist
- The compare JSON file does not exist

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
