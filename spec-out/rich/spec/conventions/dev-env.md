# Dev environment — Rich

Evidence: `pyproject.toml` (Poetry-managed), `Makefile`, `.github/workflows/`, `tests/pytest.ini`.

## Setup

```bash
poetry install        # or: pip install -e .
```

## Tests

- Framework: **pytest** (tests/ directory).
- Init: `tests/__init__.py`, `tests/conftest.py` provide scaffolding.
- Configuration: `tests/pytest.ini`.
- Run all:

```bash
poetry run pytest                 # full suite (~11k LOC across 63 files)
poetry run pytest tests/test_console.py
```

- Console-specific test file: `tests/test_console.py` (1135 LOC,
  ~50 test functions including `test_print_json*`, `test_log*`,
  `test_size*`, `test_dumb_terminal`, `test_repr`, `test_capture_*`).

## Lint / format

```bash
poetry run black .
poetry run isort .
poetry run mypy rich
```

CI (`.github/workflows/pythonpackage.yml`) runs the same on every push.

## Entry points installed by Poetry

- `python -m rich`            → `rich.__main__:main`
- `python -m rich.theme`      → theme preview
- `python -m rich.markdown`   → markdown renderer
- `python -m rich.spinner`   → spinner catalog
- `python -m rich.status`     → standalone `Status` demo

None of these live in `console.py` — they exist only in `__main__` and
sibling modules.

## Console module dependencies (build-time)

`console.py` imports from (top of file, lines 1-60):
- stdlib: `os`, `sys`, `threading`, `abc.ABC, abstractmethod`, `dataclasses`,
  `datetime`, `functools.wraps`, `itertools.islice`, `math.ceil`,
  `os.PathLike`, `time.monotonic`, `types.{FrameType, ModuleType, TracebackType}`,
  `typing.*` (incl. `Protocol`, `runtime_checkable`).
- sibling rich modules (see `layout/src.map.md`).
- Lazy: `rich.json`, `rich.pretty`, `rich._windows`, `rich._win32_console`,
  `rich._windows_renderer`, `rich.traceback`, `rich.status`, `rich.jupyter`,
  `rich.scope` — imported inside methods to avoid import-time cycles.

## Notes for a rebuild

- If testing in isolation, you must inject `_environ=` for env-var reads
  (see R-1).
- `sys.stdin/stdout/stderr` may be monkeypatched; check `rich._null_file`
  for the IO-without-real-fileno fallback.
- For Windows tests, exclude them via `pragma: no cover` or skip
  markers — the rebuild does not have to support legacy Win32 VT if
  it can detect/load the optional windows modules lazily.
