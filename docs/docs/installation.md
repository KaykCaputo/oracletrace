title: Installation
description: Install OracleTrace with pip, verify setup, and configure a virtual environment for Python performance regression tracing.
keywords: install oracletrace, install oracle trace, pip install oracletrace, python profiler install, python tracing tool install, performance regression tool, python oracle trace install, lightweight profiler setup, cli profiler install, cat logo profiler, blackcat profiler
og_title: OracleTrace Installation
og_description: Install OracleTrace with pip, verify setup, and configure a virtual environment for Python performance regression tracing.

# Installation

Install OracleTrace in under a minute and get ready to trace Python performance regressions.

## Requirements

- Python 3.10+
- `pip`

## Standard install

```bash
pip install oracletrace
```

## Verify install

```bash
oracletrace --help
```

You should see command usage, required target script, and available options.

## Recommended: use a virtual environment

```bash
python -m venv .venv
```

Activate it:

=== "Linux/macOS"

	```bash
	source .venv/bin/activate
	```

=== "Windows (PowerShell)"

	```powershell
	.venv\Scripts\Activate.ps1
	```

Then install:

```bash
pip install oracletrace
```

## Upgrade to latest version

```bash
pip install --upgrade oracletrace
```

## Dependency note

OracleTrace uses `rich` for readable terminal output and installs it automatically.

## Troubleshooting

### `oracletrace` command not found

Try running with Python module mode:

```bash
python -m oracletrace --help
```

If that works, your scripts directory is probably missing from `PATH`.

### Python version error

Check your Python version:

```bash
python --version
```

OracleTrace requires Python 3.10 or newer.