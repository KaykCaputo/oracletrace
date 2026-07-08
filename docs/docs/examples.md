title: Examples
description: Practical OracleTrace examples for local development and CI to detect Python performance regressions across runs.
keywords: oracletrace examples, oracle trace examples, python oracle trace examples, ci performance monitoring, ci regression checks, python call graph, execution trace comparison, baseline vs current trace, release performance validation, refactor performance testing, cat logo profiler, blackcat profiler
og_title: OracleTrace Examples
og_description: Practical local and CI usage patterns to detect Python performance regressions.

# Examples

Practical OracleTrace usage patterns for local development and CI performance gates.

## Basic trace run

```bash
oracletrace my_script.py
```

Best for:

- Quickly identifying heavy functions
- Understanding call flow before optimization

## Save trace data to JSON

```bash
oracletrace my_script.py --json trace.json
```

Best for:

- Keeping historical performance snapshots
- Sharing results between local and CI environments

## Save a named baseline

```bash
oracletrace baseline save my_script.py baseline.json
```

Best for:

- Creating a known-good reference from a stable branch
- Separating baseline generation from pull request validation

## Save trace data to CSV

```bash
oracletrace my_script.py --csv trace.csv
```

Best for:

- Spreadsheet analysis
- Custom dashboard ingestion

## Compare two executions

```bash
oracletrace my_script.py --json new.json --compare baseline.json
```

This highlights function-level deltas so you can catch regressions right after a change.

## Compare saved baseline files

```bash
oracletrace my_script.py --json current.json
oracletrace baseline compare baseline.json current.json --fail-on-regression --threshold 35
```

This is the recommended pattern when CI downloads or checks out a prebuilt baseline file.

## Compare two code versions

```bash
# on version A
oracletrace app.py --json v1.json

# on version B
oracletrace app.py --json v2.json --compare v1.json
```

Great for release validation and refactor checks.

## Fail the run on regression

```bash
oracletrace my_script.py --json baseline.json
oracletrace my_script.py --json current.json --compare baseline.json --fail-on-regression --threshold 25
```

This is useful in CI when you want the run to fail if performance gets worse by more than 25 percent.

Exit code behavior in this case:

- `0` when no regression exceeds threshold
- `2` when at least one regression exceeds threshold

## Print only regressions

```bash
oracletrace my_script.py --compare baseline.json --only-regressions
```

## Ignore noisy functions or files

```bash
oracletrace my_script.py --ignore ".*test.*" ".*helpers.py:debug_.*"
```

Use this to remove known noisy paths/functions from summaries and call flow.

## Focus on top offenders

```bash
oracletrace my_script.py --top 10
```

Useful when you want a concise summary of the heaviest functions.

## Lightweight CI check pattern

```bash
# stable branch or release job
oracletrace baseline save my_script.py baseline.json --repeat 50

# pull request job
oracletrace my_script.py --json current.json --repeat 50
oracletrace baseline compare baseline.json current.json --fail-on-regression --threshold 50
```

Use this when you want a simple, scriptable guardrail before merging changes.

## Trace pytest test suites

```bash
oracletrace run -- pytest tests/ -q
```

All standard options work with `run`:

```bash
oracletrace run --json baseline.json -- pytest tests/ -q
```

Best for:

- Performance regression detection in CI without test-level instrumentation
- Tracing across multiple test files with a single command

## Read the logic flow tree

Typical output shape:

```text
<module>
└── app.py:main
    ├── app.py:load_data
    └── app.py:process_data
```

This is useful for spotting unexpected call paths after feature updates.

## Tips for accurate comparisons

- Keep input data consistent between runs
- Capture a stable baseline from a clean environment
- Compare after focused changes (small PRs are easier to diagnose)
- Combine with unit tests for correctness plus performance confidence

## When OracleTrace is not the right tool

Use a profiler such as `cProfile` or `py-spy` for deep optimization sessions, production process sampling, memory analysis, or detailed call statistics. Use benchmark frameworks when you need statistically rigorous microbenchmarks. OracleTrace is optimized for fast regression signals in scripts, tests, and CI.
