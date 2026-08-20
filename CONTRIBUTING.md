# Contributing

Thank you for improving Athena CodeGraph. By participating, you agree to follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

Use Python 3.11, 3.12, or 3.13 and Git:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev,mcp,tokenizers,claude-tokenizer]"
```

Keep local IDE, assistant, database, and Athena state outside Git. The repository `.gitignore` and
`.dockerignore` cover the standard local paths.

## Before opening a pull request

```powershell
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m mypy src/athena
python -m pytest --cov=athena --cov-report=term-missing
python scripts/check_personas.py
python scripts/check_adapters.py
python scripts/check_release.py
athena benchmark benchmarks/representative.yaml --root examples/benchmark-fixture --scan --gate
```

Add focused tests for behavior changes, avoid weakening quality or security gates, and update user
documentation when commands, configuration, or compatibility changes. Pull requests should explain
the problem, the chosen design, security implications, and verification evidence.

Use GitHub Security Advisories instead of public issues for vulnerabilities.
