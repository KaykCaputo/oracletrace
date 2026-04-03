title: Examples
description: Practical OracleTrace examples for local development and CI to detect Python performance regressions across runs.
keywords: oracletrace examples, oracle trace examples, python oracle trace examples, ci performance monitoring, ci regression checks, python call graph, execution trace comparison, baseline vs current trace, release performance validation, refactor performance testing, cat logo profiler, blackcat profiler
og_title: OracleTrace Examples
og_description: Practical local and CI usage patterns to detect Python performance regressions.

# Examples

Practical OracleTrace usage patterns for local development and CI.

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

## Compare two executions

```bash
oracletrace my_script.py --json new.json --compare baseline.json
```

This highlights function-level deltas so you can catch regressions right after a change.

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

## Lightweight CI check pattern

```bash
# one-time baseline (store artifact)
oracletrace my_script.py --json baseline.json

# in CI pipeline
oracletrace my_script.py --json current.json --compare baseline.json
```

Use this when you want a simple, scriptable guardrail before merging changes.

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