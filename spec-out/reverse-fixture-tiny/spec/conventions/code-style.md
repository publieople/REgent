# Code style (inferred)

Each rule below is backed by an evidence line from the source.

## Python version

- Requires Python **≥ 3.10**.
  - Evidence: `pyproject.toml` → `requires-python = ">=3.10"`.
  - Evidence: every module starts with `from __future__ import annotations`.

## Type hints

- All public function signatures are annotated.
  - Evidence: `src/greeter/cli.py:7` (`-> argparse.ArgumentParser`).
  - Evidence: `src/greeter/core.py:7` (`-> str`).
- `__init__.py` declares `__all__`.
  - Evidence: `src/greeter/__init__.py:3`.
- `argv: list[str] | None = None` (PEP 604 union) is used.
  - Evidence: `src/greeter/cli.py:20`.

## Imports

- All greeter-internal imports use **absolute** form: `from greeter.X import Y`.
  - Evidence: `core.py:4` — `from greeter.formats import format_default, format_with_lang`.
- No relative imports anywhere (`grep -rn 'from \\.' src/` returns nothing).

## Naming

- Module: `snake_case`.
- Public API: `snake_case`.
- Constants: none defined.

## String formatting

- f-strings everywhere.
  - Evidence: `formats.py:8` (`f"Hello, {name}!"`).
- CLI error text format: `f"error: {exc}"`.

## Error handling

- Domain errors raised as `ValueError`, not custom subclasses.
  - Evidence: `core.py:13` (`raise ValueError(...)`).
- CLI catches `ValueError` and returns exit code `2`.

## Test style

- Plain `def test_*` functions, no classes.
  - Evidence: `tests/test_greeter.py` (all 8 functions are top-level).
- Uses `pytest.raises` for negative cases.
