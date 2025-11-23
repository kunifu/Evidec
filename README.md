# Evidec (WIP)

Evidence-based A/B test helper in Python. Run statistical tests, decide GO/NO-GO via rules, and emit Markdown evidence reports.

## Requirements
- Python 3.10+ (uses structural pattern matching and modern typing)
- Recommended installer: [uv](https://github.com/astral-sh/uv) (pip compatible)

## Quick start
```bash
# create and activate a virtualenv (uv will create .venv by default)
uv venv
source .venv/bin/activate

# install library + dev tools (ruff, mypy, pytest, poethepoet)
uv pip install -e '.[dev]'

# or with pip
pip install -e '.[dev]'
```

## Developer tasks (poethepoet)
- `poe lint`      – ruff check
- `poe format`    – ruff format
- `poe typecheck` – mypy evidec
- `poe test`      – pytest -q
- `poe check`     – lint + typecheck + test

## Project layout (planned)
```
evidec/
  __init__.py
  core/
    experiment.py
    decision_rule.py
    report.py
  stats/
    ztest.py
    ttest.py
  report/
    renderer.py
examples/
  basic_ab.py
tests/
```

## Status
- Environment scaffolded (pyproject, tasks, lint/type/test config).
- Core implementation and tests are upcoming; see `aiNote/02_MVP_design.md` for design details and task list.

## License
MIT License (see LICENSE).
