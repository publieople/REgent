# src.map — file → purpose → public API

## `src/greeter/__init__.py`

**Purpose**: package facade.
**Public API**:
- `__version__ = "0.1.0"`
- Re-exports `greet`, `shout_greet`, `format_default`, `format_with_lang`.
**Side effects**: none.

## `src/greeter/core.py`

**Purpose**: greeting logic. Owns input validation and language dispatch.
**Public API**:
- `greet(name: str, lang: str = "en") -> str`
  - Strips surrounding whitespace.
  - Raises `ValueError` on empty/whitespace name.
  - `lang == "en"` → `format_default(name)`; otherwise → `format_with_lang(name, lang)`.
- `shout_greet(name: str, lang: str = "en") -> str`
  - Returns `greet(...).upper()`.
**Side effects**: none.
**Imports**: `from greeter.formats import format_default, format_with_lang`.

## `src/greeter/formats.py`

**Purpose**: output formatting. Pure functions, no validation.
**Public API**:
- `format_default(name: str) -> str` → `"Hello, {name}!"`.
- `format_with_lang(name: str, lang: str) -> str` →
  looks up `{"en", "es", "fr", "zh"}`. Unknown → `format_default(name)`.
**Side effects**: none.

## `src/greeter/cli.py`

**Purpose**: argparse CLI. Pure dispatch — does not import any internal
re-implementation; delegates to `greeter.core`.
**Public API**:
- `build_parser() -> argparse.ArgumentParser` — programmatic parser.
- `main(argv: list[str] | None = None) -> int` — returns exit code.
  - Positional `name`.
  - `--lang {en,es,fr,zh}` (default `en`).
  - `--shout` flag toggles `shout_greet` vs `greet`.
  - `ValueError` is caught and printed to stderr; returns `2`.
  - Success → `0`.
**Module-level**: `if __name__ == "__main__": SystemExit(main())`.

## `tests/test_greeter.py`

**Purpose**: full coverage of public API.
**Tests** (8 total):
1. `test_default_format` — `format_default("Ada") == "Hello, Ada!"`.
2. `test_format_with_lang_spanish` — `format_with_lang("Ada", "es") == "Hola, Ada!"`.
3. `test_format_with_lang_unknown_falls_back`.
4. `test_greet_strips_whitespace` — surrounding spaces removed.
5. `test_greet_rejects_empty` — raises `ValueError`.
6. `test_greet_rejects_whitespace_only` — raises `ValueError`.
7. `test_shout_greet` — uppercase English.
8. `test_shout_greet_spanish` — uppercase Spanish.

## `pyproject.toml`

**Purpose**: project metadata + build + script registration.
**Build**: setuptools ≥ 61, PEP 517.
**Console script**: `greeter = "greeter.cli:main"`.
**Packages discovered under**: `src/`.

## `README.md`

**Purpose**: quick start with two `greeter` CLI examples + `pytest`.
