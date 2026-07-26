# Architecture rules — Rich Console

Evidence is line-anchored to `rich/console.py`.

## Threads & state

- **Per-thread buffer.** `ConsoleThreadLocals(threading.local)` — lines 535-541.
  Holds `theme_stack`, `buffer: list[Segment]`, `buffer_index: int`.
- **Two locks.** `self._lock = threading.RLock()` (line 714) for
  `_render_hooks` / `_live_stack`. `self._record_buffer_lock = threading.RLock()`
  (line 744) for record-buffer reads/writes.
- **Nested buffer scopes.** `_buffer_index` is per-thread; only flush at 0
  (line 2067: `if self._buffer_index == 0:`).
- **Thread-local _buffer access via properties** (lines 770-787) — never
  read `self._thread_locals` directly from outside `Console`.

## Error policy

- All cross-call errors (NotRenderableError, NoAltScreen, MissingStyle,
  StyleSyntaxError, LiveError, CaptureError) are custom, in `rich.errors`
  or local. They MUST inherit from `Exception` (use `errors.NoAltScreen`,
  not bare `RuntimeError`).
- `on_broken_pipe()` is an OVERRIDE POINT — explicitly designed to be
  subclassed (line 2035).
- `BrokenPipeError` is converted to `SystemExit(1)`. NEVER swallow it
  silently.

## Capability gating

These methods MUST be no-ops when the capability is unavailable:

| Method | Gate |
|---|---|
| `control(...)` | `not self.is_dumb_terminal` (line 1616) |
| `show_cursor` | `self.is_terminal` (line 1196) |
| `set_alt_screen` | `is_terminal and not legacy_windows` (line 1216) |
| `set_window_title` | `self.is_terminal` (line 1258) |

Stubs MUST still return the documented bool so the caller can branch on
"did this happen".

## Render dispatch invariants

- `Console.render` is the **only** function that turns renderables into
  `Segment`s. Helpers like `render_lines`, `print`, `log`, `capture`
  delegate to it.
- Strings always go through `render_str` (line 1320-1324).
- `render_str` may set `markup_enabled` to False to bypass
  `rich.markup.render` (lines 1437-1460).
- `not isinstance(renderable, type)` matters — types must not be silently
  rendered (line 1318).

## Recording invariants

- `record=True` ⇒ `_record_buffer` filled as a SIDE EFFECT of
  `_write_buffer()` whenever `_buffer_index == 0`. (Lines 2062-2065.)
- All exporters assert `self.record` (lines 2204-2206, 2268-2270, etc.).
- `export_text(styles=True)` may include ANSI; `styles=False` MUST drop
  control-only segments.

## Broken-pipe invariant

Broken-pipe handling is intentionally one-way:
`on_broken_pipe` MUTATES global stdout via `os.dup2(devnull, ...)` and
`SystemExit(1)`. Tests that exercise it MUST restore stdout
(use a saved copy of `sys.stdout`) and capture SystemExit.

## Style / no_color / legacy_windows plumbing

- `no_color` ⇒ `_render_buffer` calls `Segment.remove_color` before emit
  (line 2139).
- `legacy_windows` ⇒ on Windows, the write path takes a different branch
  (line 2076).
- `self.style` (constructor kwarg) is applied LAST in
  `_collect_renderables` (line 1583); overrides per-call `style=` arg.

## __dunder__ gotchas

- `__rich__` and `__rich_console__` and `__rich_measure__` are part of
  the protocol; `Console.render` looks them up via `hasattr`.
- Class objects (`isinstance(renderable, type)`) skip `__rich_console__`
  to avoid rendering the class itself (line 1318).
