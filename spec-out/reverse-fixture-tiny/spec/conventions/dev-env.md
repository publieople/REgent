# Dev environment (inferred)

## Build / install

- Tool: `pip install -e .` from repo root.
- Build backend: `setuptools.build_meta` (PEP 517).
  - Evidence: `pyproject.toml` → `[build-system]`.

## Test

- Framework: **pytest**.
- Command: `pytest` (from repo root) runs `tests/test_greeter.py`.
- No `conftest.py`, no `pytest.ini`, no `[tool.pytest.ini_options]` in
  `pyproject.toml` — defaults are accepted.

## CLI invocation during dev

- After `pip install -e .`:
  - `greeter Ada`
  - `greeter Ada --lang es`
  - `greeter Ada --shout`

## Linting / formatting

- No Black/Ruff/mypy config present. Conventions are inferred from source
  rather than enforced by a tool.
