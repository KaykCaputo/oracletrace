## Summary

Describe what this PR changes and why.

## Related Issue

Link the related issue if available.

Example: Closes #123

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor
- [ ] Documentation update
- [ ] CLI behavior change

## What Changed

List the key changes in a few bullets.

-
-
-

## Validation

Describe how you validated this change.

### CLI smoke check

```bash
oracletrace --help
```

### Functional trace run

```bash
oracletrace your_script.py
```

### JSON export and compare flow

```bash
oracletrace your_script.py --json baseline.json
oracletrace your_script.py --json current.json --compare baseline.json
```

### CSV, ignore, and top flags

```bash
oracletrace your_script.py --csv trace.csv
oracletrace your_script.py --ignore ".*helper_function.*" "debug_.*"
oracletrace your_script.py --top 10
```

### Docs build (if docs changed)

```bash
mkdocs build -f docs/mkdocs.yml
```

## Checklist

- [ ] The code follows style conventions.
- [ ] I added unit tests for the new functionality.
- [ ] CI (GitHub Actions) is green.
- [ ] I updated documentation/README when needed.

## Before/After Output (if applicable)

Include relevant CLI output snippets when behavior or formatting changed.

### Before

```text

```

### After

```text

```

## Additional Notes

Anything reviewers should pay special attention to.
