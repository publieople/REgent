# Rich (Textualize/rich) — Console module overview

**Repository:** https://github.com/Textualize/rich
**Reverse scope:** `rich/console.py` only (single module, in-file helpers).
**Other modules:** Treat `Segment`, `Text`, `Style`, `Theme`, `Control`, `Group`,
`LogRender`, `Pager`, `Screen`, `Measure`, `Status`, `Live`, `Traceback`, `JSON`,
`pretty.Pretty` as **external dependencies** with their existing public
interfaces. Do not re-implement them.

Rich is a Python library for *rich* text and beautiful formatting in the
terminal. `Console` is its central abstraction: a thread-safe, recording-aware,
Jupyter-aware, ANSI-rendering sink that accepts strings, renderables, and
Python objects and emits styled segments to a stream.

Key entry points that users will care about:

- `class rich.console.Console` — the workhorse.
- `Console.print(...)`, `Console.log(...)`, `Console.print_json(...)`,
  `Console.print_exception(...)`, `Console.rule(...)`, `Console.status(...)`.
- Context managers: `Console.capture()`, `Console.pager()`, `Console.screen()`,
  `Console.use_theme(...)`, and bare `with Console():` buffer scope.
- Recording/export: `Console.record=True`, then `export_text` / `save_text` /
  `export_html` / `save_html` / `export_svg` / `save_svg`.

The module also defines:

- `ConsoleDimensions` (NamedTuple: width, height in cells/lines).
- `ConsoleOptions` (dataclass: render-time knobs; immutable copy/update API).
- `NoChange` sentinel + `NO_CHANGE` instance.
- `CaptureError` exception.
- `NewLine`, `ScreenUpdate`, `Capture`, `ThemeContext`, `PagerContext`,
  `ScreenContext`, `Group`, `group()` decorator.
- `RichCast` and `ConsoleRenderable` `Protocol`s (runtime-checkable).
- Public type aliases: `RenderableType`, `RenderResult`, `HighlighterType`,
  `JustifyMethod` ("default" | "left" | "center" | "right" | "full"),
  `OverflowMethod` ("fold" | "crop" | "ellipsis" | "ignore").
- Constants: `JUPYTER_DEFAULT_COLUMNS=115`, `JUPYTER_DEFAULT_LINES=100`,
  `WINDOWS = sys.platform=="win32"`, `COLOR_SYSTEMS` dict.
- Helpers: `_is_jupyter`, `get_windows_console_features`, `detect_legacy_windows`.

CLI entry points: `python -m rich`, `rich.spinner`, `rich.status`,
`rich.markdown`, `rich.theme`. None of these live in `console.py`; they are
references in this spec only.
