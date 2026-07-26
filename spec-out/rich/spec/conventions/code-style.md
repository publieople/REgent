# Code style — Rich

All evidence is `pyproject.toml` lines 40-72 unless noted.

## Formatter

- **black** — pinned `^22.6` (line 40). 4-space indent, double quotes.
- **isort** — pinned to `black` profile (lines 67-68).

## Type checker

- **mypy** — pinned `^1.11` (line 41). `[[tool.mypy.overrides]]` block
  enables `check_untyped_defs = True`. Strict-ish but not `--strict`.

## Filename

- Public APIs live in `rich/<noun>.py` (e.g. `console.py` → `class Console`).
- Private helpers use a leading underscore in both filename (`_fileno.py`,
  `_log_render.py`, `_export_format.py`) and symbol names.

## Conventions within `rich/console.py`

- Constants at module top, before any class: `JUPYTER_DEFAULT_COLUMNS`,
  `JUPYTER_DEFAULT_LINES`, `WINDOWS`, `HighlighterType`, `JustifyMethod`,
  `OverflowMethod` (lines 64-70).
- File-descriptor ints captured at import time with try/except
  (lines 79-90); never accessed lazily.
- All renderable context managers (`Capture`, `ThemeContext`, `PagerContext`,
  `ScreenContext`) are themselves small classes, not `@contextmanager`s —
  internal mutable state (e.g. `Capture._result`) needs persistence.
- Docstrings on every `Console` method follow Google's format with
  `Args:` / `Returns:` / `Raises:` blocks (e.g. lines 1669-1687 `print`).
- Long signatures use keyword-only arguments with `*,` separators
  (e.g. `__init__` at line 619-651).
- `assert` is used for developer-facing invariants (e.g. `Console.render`
  line 1143 `assert count >= 0`; exporters `assert self.record`).
- `# pragma: no cover` annotations on lines that test frameworks cannot
  reach (Windows-only, Jupyter-only, idle-only).
- Private functions/variables prefixed `_`; the `__` style is reserved for
  protocols (`__rich__`, `__rich_console__`, `__rich_measure__`).
- Type aliases (`RenderableType`, `RenderResult`, `HighlighterType`) declared
  at module level using `Union[...]` rather than `X | Y` (target supports
  older Python).
