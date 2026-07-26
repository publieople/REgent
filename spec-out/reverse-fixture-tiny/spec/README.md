# greeter (spec view)

A small Python 3.10+ package that produces greeting strings, with optional
localization and an optional upper-case mode. Ships a CLI entry point and a
pytest test suite.

Source repository: https://github.com/publieople/reverse-fixture-tiny
Reversed by: REgent regent-reverse v0.1.0

## Public surface

- Python API (in `greeter` package):
  - `greet(name: str, lang: str = "en") -> str`
  - `shout_greet(name: str, lang: str = "en") -> str`
  - `format_default(name: str) -> str`
  - `format_with_lang(name: str, lang: str) -> str`
- CLI: `greeter <name> [--lang en|es|fr|zh] [--shout]`

## Layout (8 source files)

- `src/greeter/__init__.py` — package facade, exposes `__version__`.
- `src/greeter/core.py` — `greet`, `shout_greet`.
- `src/greeter/formats.py` — output format functions.
- `src/greeter/cli.py` — argparse CLI; also returns exit codes.
- `tests/test_greeter.py` — 8 pytest cases.
- `pyproject.toml` — setuptools build, console script `greeter`.
- `README.md`, `LICENSE` (MIT).
