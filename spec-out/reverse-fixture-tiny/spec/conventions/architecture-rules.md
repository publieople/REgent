# Architecture rules (inferred)

## Module layering

```
core      → formats
cli       → core
__init__  → core, formats
```

Rules:

- `core` MUST NOT import from `cli`.
- `formats` MUST NOT import from `core` or `cli`.
- All cross-module imports use the absolute `greeter.<module>` form.
  - Evidence: `core.py:4`.

## Pure functions

- `formats.py` is pure (no I/O, no global state).
  - Evidence: 19 lines, only function defs and a `dict` literal.

## CLI exit codes

- `0` = success.
- `2` = domain input error (`ValueError`).
  - Evidence: `cli.py:25` (`return 2`).

## Console-script entry

- Registered in `pyproject.toml` as
  `greeter = "greeter.cli:main"`.
