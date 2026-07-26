# Spec — `rich.console` (Console + helpers)

## Purpose

Provide a thread-safe, environment-aware sink that converts renderables
(strings, numbers, `__rich_console__`-supporting objects, or anything
`Pretty`-can-format) into an ANSI-styled byte stream on the terminal and
mirrors the same output to optional HTML/SVG/text record buffers.

The module also exposes reusable context managers (`Capture`, `Pager`,
`Screen`, `Theme`, plus the implicit buffer scope `with Console():`) and the
rendering protocols (`RichCast`, `ConsoleRenderable`) that the rest of the
Rich ecosystem implements.

## Requirements

### R-1 Construction & capability detection

The class MUST honor these `__init__` kwargs (keyword-only) and resolve
defaults in this exact order. References are to lines in the original.

| Kwarg | Default | Resolution |
|---|---|---|
| `color_system` | `"auto"` | `"auto"` → `_detect_color_system()`; else `COLOR_SYSTEMS[color_system]`. |
| `force_terminal` | `None` | Truthy stores `_force_terminal`; `is_terminal` returns it. |
| `force_jupyter` | `None` | Truthy/falsy overrides `_is_jupyter()`. |
| `force_interactive` | `None` | When None, read `TTY_INTERACTIVE` env: `"0"/"1"` map to False/True. |
| `soft_wrap` | `False` | Used by `print()` to derive `no_wrap=True, overflow="ignore", crop=False`. |
| `theme` | `None` | Becomes top of `ConsoleThreadLocals.theme_stack`. |
| `stderr` | `False` | `file` defaults to `sys.stderr` instead of `sys.stdout`. |
| `file` | `None` | Optional `IO[str]`; falls back to `NULL_FILE` when stderr also None. |
| `quiet` | `False` | If True, `_check_buffer` discards `_buffer`. |
| `width` | `None` | Reads `JUPYTER_COLUMNS` (in jupyter) or `COLUMNS` env (must be all-digits). |
| `height` | `None` | Same with `JUPYTER_LINES` / `LINES`. |
| `style` | `None` | Applied to all renderables inside `_collect_renderables` via `Styled`. |
| `no_color` | `None` | Defaults to `bool(_environ.get("NO_COLOR"))`. |
| `tab_size` | `8` | Stored on self; consumers (e.g. text) read it. |
| `record` | `False` | If True, `_write_buffer` mirrors output into `_record_buffer`. |
| `markup` / `emoji` / `highlight` | `True` | Str-bool defaults; may be overridden by per-call kwargs. |
| `emoji_variant` | `None` | `"text"` or `"emoji"` (from `rich.emoji.EmojiVariant`). |
| `log_time` / `log_path` | `True` | Passed to `LogRender`. |
| `log_time_format` | `"[%X]"` | strftime OR a `FormatTimeCallable`. |
| `highlighter` | `ReprHighlighter()` | `Callable[[str|Text], Text]`. |
| `legacy_windows` | `None` | Defaults to `detect_legacy_windows() and not is_jupyter`. |
| `safe_box` | `True` | Hint for downstream renderables. |
| `get_datetime` | `datetime.now` | Callable returning `datetime`. |
| `get_time` | `monotonic` | Callable returning `float` seconds. |
| `_environ` | `None` | When given, replaces `os.environ` snapshot (used for testing). |

Storage (lines 714-751) MUST create:
- `self._lock = threading.RLock()`
- `self._record_buffer_lock = threading.RLock()`
- `self._thread_locals = ConsoleThreadLocals(theme_stack=ThemeStack(themes.DEFAULT if theme is None else theme))`
- `self._record_buffer: list[Segment] = []`
- `self._render_hooks: list[RenderHook] = []`
- `self._live_stack: list[Live] = []`
- `self._is_alt_screen = False`

### R-2 Immutable options object

`ConsoleOptions` MUST be a `@dataclass`; all mutators MUST return a fresh
instance via `ConsoleOptions.__new__` + `dict.copy()` (see `copy`, line 147-155).
- `ascii_only` = `not encoding.startswith("utf")`.
- `update(width, ...)` MUST treat every kwarg whose value IS-A `NoChange` as
  "leave alone".
- `update(width=int)` MUST set BOTH `min_width` and `max_width = max(0, width)`.

### R-3 Buffer & threading model

- `self._buffer` / `self._buffer_index` MUST be properties that read/write
  `self._thread_locals` (R-1 above) so per-thread state is isolated.
- `_enter_buffer` / `_exit_buffer` MUST increment/decrement the
  thread-local `_buffer_index`.
- `_write_buffer` MUST only flush when `_buffer_index == 0` on the
  calling thread.
- All mutations of `_render_hooks` / `_live_stack` MUST be guarded by
  `with self._lock`.
- `_record_buffer` mutation MUST use a separate `_record_buffer_lock`.

### R-4 Render dispatch

`Console.render(renderable, options=None) -> Iterable[Segment]` MUST, in order
(lines 1310-1343):
1. Use `options or self.options`; if `max_width < 1`, yield nothing.
2. Call `rich_cast(renderable)` (per `rich.protocol`).
3. If the result has `__rich_console__` (and isn't a type), call it.
4. Else if it's a `str`, build via `render_str(...)` and call its `__rich_console__`.
5. Else raise `errors.NotRenderableError("Unable to render {renderable!r}; A str, Segment or object with __rich_console__ method is required")`.
6. Wrap the returned iterator in `try: iter(...) except TypeError: raise NotRenderableError(...)`.
7. For each yielded item: if it's a `Segment`, yield it; else recurse `self.render(item, options.reset_height())`.

### R-5 `print()` & `log()` semantics

`print(*objects, sep=" ", end="\n", **opts)` MUST (lines 1689-1756):
1. If `not objects`: convert `end` to a single `NewLine()` (when default) or `""`.
2. If `soft_wrap`: force `no_wrap=True, overflow="ignore", crop=False` UNLESS
   those came in as non-None.
3. Snapshot `self._render_hooks[:]` and operate inside `with self:` (buffer scope).
4. Compute renderables via `_collect_renderables(objects, sep, end, ...)`.
5. Run each hook's `process_renderables` (may mutate list).
6. Build `render_options = self.options.update(justify=..., overflow=..., width=min(width, self.width) if width else NO_CHANGE, height=height, no_wrap=no_wrap, markup=markup, highlight=highlight)`.
7. If `style is None`: render each renderable, extend `new_segments`.
   Else: split each render output by `Segment.split_lines_terminator`, apply
   `Segment.apply_style(line, render_style)`, append `Segment.line()` between lines.
8. If `new_line_start` and the rendered output has >1 line: insert `Segment.line()` at index 0.
9. If `crop`: push each `Segment.split_and_crop_lines(new_segments, self.width, pad=False)` chunk to `self._buffer`. Else push `new_segments` raw.

`log(...)` is structurally identical but decorates renderables with `_log_render`
(time+path:line) using `_caller_frame_info(_stack_offset)` (R-7).

### R-6 Capture / Pager / Screen / Theme CMs

- `Capture`: `__enter__` → `console.begin_capture()`; `__exit__` → `result = console.end_capture()` (stores `self._result`); `get()` returns that string or raises `CaptureError("Capture result is not available until context manager exits.")`.
- `PagerContext`: enters via `_enter_buffer`; on a clean exit, joins `_buffer`, optionally `strip_styles`/`strip_links`, hands `content = _render_buffer(...)` to `pager.show(content)`; ALWAYS calls `_exit_buffer`.
- `ScreenContext`: enter calls `set_alt_screen(True)`; if that returned True and `hide_cursor`, calls `show_cursor(False)`. Exit reverses. `.update(*renderables, style=None)` overwrites `self.screen.renderable` and prints the screen, no end.
- `ThemeContext`: `push_theme(theme, inherit)` / `pop_theme()`.
- `Console.__enter__/__exit__` are buffer scopes: `_enter_buffer` / `_exit_buffer`.

### R-7 `_caller_frame_info`

Static. `offset += 1` (skip the helper). Uses `inspect.currentframe()` unless
injected. Walks `frame.f_back` `offset` times; asserts the final `frame is not None`.
Returns `Tuple[str, int, Dict[str, Any]]` of `(filename, lineno, locals)`.

### R-8 Output write path

`_check_buffer()`:
1. If `quiet`: `del self._buffer[:]` and return.
2. Try `_write_buffer()`; on `BrokenPipeError`: call `self.on_broken_pipe()`.

`_write_buffer()` (lines 2059-2130):
1. Acquire `_lock`.
2. If `self.record` and `_buffer_index == 0`: append `self._buffer[:]` (a copy) to `_record_buffer` under `_record_buffer_lock`.
3. If `_buffer_index != 0`: return (deferred).
4. If `self.is_jupyter`: `from .jupyter import display(self._buffer, self._render_buffer(self._buffer[:]))`; clear buffer. (Out-of-process: not rebuild-tested.)
5. Else if `WINDOWS`:
   - legacy Windows AND `fileno` in `_STD_STREAMS_OUTPUT` AND fileno is not None: use `LegacyWindowsTerm(self.file)` + `legacy_windows_render(...)`; respect `no_color` (strip colors via `Segment.remove_color`).
   - Else: text = `self._render_buffer(self._buffer[:])`. Write in ≤`MAX_WRITE = 32*1024//4` byte chunks (splitlines-keepends). Reraise any `UnicodeEncodeError` after replacing `error.reason` with `f"{error.reason}\n*** You may need to add PYTHONIOENCODING=utf-8 to your environment ***"`.
6. Else (POSIX): same `UnicodeEncodeError` wrap; otherwise `self.file.write(text); self.file.flush(); del self._buffer[:]`.

`_render_buffer(buffer)` (lines 2132-2154):
- Honors `no_color` via `Segment.remove_color`.
- For each `(text, style, control)` in buffer:
  - If `style`: append `style.render(text, color_system=..., legacy_windows=...)`.
  - Elif NOT (`not self.is_terminal AND control`): append `text`. (So plain control codes on a non-terminal are dropped.)
- Returns `"".join(parts)`.

### R-9 Broken-pipe handling

`on_broken_pipe()` MUST (lines 2030-2042):
1. Set `self.quiet = True`.
2. `os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())`.
3. `raise SystemExit(1)`.

### R-10 Exporters

All four exporters MUST `assert self.record, "To export console contents set record=True in the constructor or instance"`.
All four MUST acquire `self._record_buffer_lock` for the duration of read,
and if `clear=True` `del self._record_buffer[:]` at the end.

| Method | What it returns / writes |
|---|---|
| `export_text(*, clear=True, styles=False) -> str` | If `styles`: `"".join(style.render(text) if style else text for text,style,_ in _record_buffer)`. Else: `"".join(s.text for s in _record_buffer if not s.control)`. |
| `save_text(path, *, clear=True, styles=False)` | `open(path, "w", encoding="utf-8").write(self.export_text(...))`. |
| `export_html(*, theme=None, clear=True, code_format=None, inline_styles=False) -> str` | Default `code_format = CONSOLE_HTML_FORMAT`. Iterates `Segment.filter_control(Segment.simplify(_record_buffer))`; escape text with `html.escape`; with `inline_styles=True` emit `<span style="...">`/`<a href="...">`. Else build a `.rN{}` stylesheet + `<span class="rN">`. Substitute `{code/stylesheet/foreground/background}` in `code_format`. `theme` defaults to `DEFAULT_TERMINAL_THEME`. |
| `save_html(path, *, theme=None, clear=True, code_format=CONSOLE_HTML_FORMAT, inline_styles=False)` | Wraps `export_html`. |
| `export_svg(*, title="Rich", theme=None, clear=True, code_format=CONSOLE_SVG_FORMAT, font_aspect_ratio=0.61, unique_id=None) -> str` | Lines 2352-2604; uses `zlib.compress`, `html.escape`, `rich.cells.cell_len`. Produces a string substituted into `code_format`. |
| `save_svg(path, *, ...)` | Wraps `export_svg`. |

### R-11 Type protocols

`RichCast` and `ConsoleRenderable` MUST be declared with
`@runtime_checkable` and define the duck-typed methods shown in
`layout/src.map.md`. (No runtime logic; this is a type contract.)

### R-12 Helpers

- `_is_jupyter()` MUST return True when `get_ipython` is defined AND its
  class indicates Jupyter/Colab/Databricks; False for terminal IPython.
- `detect_legacy_windows()` MUST return `WINDOWS and not get_windows_console_features().vt`.
- `get_windows_console_features()` MUST lazily import `from ._windows import get_windows_console_features` and cache the module-global result.

### R-13 Human-facing literals

The rebuild must reproduce these BYTE-EXACT strings when they appear:

- Error prefixes (all from the source):
  - `Capture result is not available until context manager exits.`
  - `json must be str. Did you mean print_json(data={!r}) ?`
  - `Alt screen must be enabled to call update_screen`
  - `Failed to get style {!r}; {}`
  - `Unable to render {!r}; A str, Segment or object with __rich_console__ method is required`
  - `object {!r} is not renderable`
  - `To export console contents set record=True in the constructor or instance`
- The two `UnicodeEncodeError` rewrites:
  - `{original_reason}\n*** You may need to add PYTHONIOENCODING=utf-8 to your environment ***`
- `_log_render` strftime default: `"[%X] "` is implied by `log_time_format="[%X]"`; the prefix `[\x1b[2m`/`\x1b[0m]` is in `_log_render.py`, NOT `console.py`, so it is OUT OF SCOPE here.
- `__repr__`: `<console width={self.width} {self._color_system!s}>`

## Scenarios

> WHEN-style scenarios. Each ends in a checkable assertion.

**S-1** WHEN `Console(file=io.StringIO(), width=80)` is constructed,
THEN `console.file.write` later receives the rendered segments (no ANSI on
non-terminal by default — though overrideable via `force_terminal=True`).

**S-2** WHEN `print(*objects)` is called on a console with
`is_terminal=False, force_terminal=False`, THEN control-only segments
MUST be skipped (`_render_buffer` line 2150).

**S-3** WHEN `print("[bold]X[/]")` is called on `markup=True` console,
THEN `render_markup` produces `Text` containing the bold style; bare
brackets `[]` are interpreted as markup delimiters.

**S-4** WHEN a renderable's `__rich_console__` yields a non-`Segment`,
THEN `Console.render` MUST recursively call itself with
`options.reset_height()` (line 1338).

**S-5** WHEN `quiet=True`, THEN `_check_buffer` MUST drain
`self._buffer` (length → 0) and never call `_write_buffer`.

**S-6** WHEN `record=True` AND `_buffer_index == 0`, THEN `_write_buffer`
MUST append `_buffer[:]` to `_record_buffer` under `_record_buffer_lock`.

**S-7** WHEN an exporter is called without `record=True`, THEN it MUST
raise `AssertionError` with the literal message
`To export console contents set record=True in the constructor or instance`.

**S-8** WHEN `print()` raises `BrokenPipeError` inside `_check_buffer`,
THEN `on_broken_pipe` runs, sets quiet, dup2's stdout to devnull, and
`SystemExit(1)` is raised.

**S-9** WHEN `Console.out(...)` is called, THEN it MUST compose a single
string via `sep.join(str(o) for o in objects)` and forward to `print`
with `emoji=False, markup=False, no_wrap=True, overflow="ignore", crop=False` — no pretty-printing.

**S-10** WHEN `Console.status("loading")` enters as a CM AND
`is_terminal=False`, THEN Status still returns a CM but no spinner animates
(no spec — depends on Live implementation; OUT OF SCOPE here).

**S-11** WHEN `capture()` returns its CM object, AND `__exit__` runs cleanly,
THEN `capture.get()` returns the rendered string and the file was not
written during the with block.

**S-12** WHEN `pager()` exists AND `__exit__` runs cleanly,
THEN `pager.show(_render_buffer(stripped_segments))` is called.

**S-13** WHEN `is_dumb_terminal=True`, THEN `control()` MUST be a no-op
(strips cursor moves; bell/clear still emitted by dedicated calls).

**S-14** WHEN `_collect_renderables` receives `objects=[1, 2, 3, "abc"]`,
THEN ints get joined into one Text via highlighter; `abc` joined with same.

**S-15** WHEN `print_json(data={...}, indent=2)` is called, THEN output
MUST be valid JSON (round-trips via `json.loads`).

**S-16** WHEN `force_terminal=True` on a non-TTY `file`,
THEN `is_terminal` MUST return True and ANSI codes emitted.

**S-17** WHEN `NO_COLOR` env non-empty AND `no_color=None`,
THEN `self.no_color` MUST be True; `_render_buffer` MUST call
`Segment.remove_color` before emitting.

## Out of scope (this module)

- `rich.json`, `rich.status`, `rich.traceback`, `rich.scope`, `rich.live`,
  `rich.pretty`, the `_win32_console`, `_windows`, `_windows_renderer`,
  `_log_render` modules — referenced by name; their internals are NOT part
  of this spec.
- `__main__` demo block (lines 2645-2698): present in source, not part of
  the contract.
- `python -m rich` / `rich.cli` / `rich.markdown` / `rich.spinner` CLI —
  these are sibling entry points living in `rich/__main__.py`,
  `rich/_loop.py`, etc., not in `console.py`.
