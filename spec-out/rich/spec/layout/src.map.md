# src.map.md — `rich/console.py`

**Role:** the high-level terminal interface. Most users only ever need this one
class.  **Size:** ~2 698 LOC, 100 public methods on `Console`.  **Tests:**
`tests/test_console.py` (1 135 LOC, ~50 `test_*` functions covering color
detection, options, init, print, json, log, capture, record/export, screen,
status, pager, alt-screen, exception printing, broken-pipe).

## Module-level

| Name | Lines | Purpose |
|---|---|---|
| `JUPYTER_DEFAULT_COLUMNS=115` | 64 | Fallback width in Jupyter when `JUPYTER_COLUMNS` unset. |
| `JUPYTER_DEFAULT_LINES=100` | 65 | Same, for height. |
| `WINDOWS = sys.platform=="win32"` | 66 | Cached at import. |
| `HighlighterType` | 68 | `Callable[[Union[str, Text]], Text]`. |
| `JustifyMethod` | 69 | `"default" \| "left" \| "center" \| "right" \| "full"`. |
| `OverflowMethod` | 70 | `"fold" \| "crop" \| "ellipsis" \| "ignore"`. |
| `class NoChange` + `NO_CHANGE` | 73-77 | Sentinel; passed through `ConsoleOptions.update(*, width=NO_CHANGE, ...)`. |
| `_STDIN/_STDOUT/_STDERR_FILENO` | 79-90 | Captured at import with try/except. |
| `_STD_STREAMS`, `_STD_STREAMS_OUTPUT` | 92-93 | Tuples of ints. |
| `_TERM_COLORS` | 96-100 | Map `kitty/256color/16color → ColorSystem`. |
| `class ConsoleDimensions(NamedTuple)` | 103-109 | `(width, height)` cells/lines. |
| `class ConsoleOptions` (dataclass) | 112-243 | Immutable render knob bag. Methods: `copy`, `update`, `update_width`, `update_height`, `reset_height`, `update_dimensions`. Property `ascii_only`. |
| `class RichCast(Protocol, @runtime_checkable)` | 246-253 | Has `__rich__() -> Union[ConsoleRenderable, RichCast, str]`. |
| `class ConsoleRenderable(Protocol, @runtime_checkable)` | 256-263 | Has `__rich_console__(console, options) -> RenderResult`. |
| `RenderableType` (alias) | 267 | `Union[ConsoleRenderable, RichCast, str]`. |
| `RenderResult` (alias) | 271 | `Iterable[Union[RenderableType, Segment]]`. |
| `class CaptureError` | 276-277 | `Capture.get()` before exit. |
| `class NewLine` | 280-289 | Counts N newlines via `__rich_console__`. |
| `class ScreenUpdate` | 292-307 | Repositions lines at (x, y) via `Control.move_to`. |
| `class Capture` | 310-340 | CM that calls `begin_capture`/`end_capture`; `.get()` returns str. |
| `class ThemeContext` | 343-361 | CM wrapping `push_theme`/`pop_theme`. |
| `class PagerContext` | 364-400 | CM buffer → `Pager.show(content)`. |
| `class ScreenContext` | 403-447 | CM alt-screen; `.update(*renderables, style=...)`. |
| `class Group` | 450-480 | Tuple of renderables; `fit=True` measures to contents. |
| `def group(fit=True)` | 483-502 | Decorator: wraps a method returning `Iterable[RenderableType]`. |
| `def _is_jupyter()` | 505-522 | Detects ZMQ/Jupyter/colab/databricks. |
| `COLOR_SYSTEMS` | 525-530 | `"standard"\|"256"\|"truecolor"\|"windows" → enum`. |
| `_COLOR_SYSTEMS_NAMES` | 532 | Reverse map (enum → name). |
| `class ConsoleThreadLocals(threading.local)` | 535-541 | Holds `theme_stack`, `buffer`, `buffer_index`. |
| `class RenderHook(ABC)` | 544-560 | Override `process_renderables(list) -> list`. |
| `_windows_console_features` | 563 | Module-global cache. |
| `def get_windows_console_features()` | 566-573 | Lazy import from `._windows`. |
| `def detect_legacy_windows()` | 576-578 | `WINDOWS and not features.vt`. |
| `class Console` | **581-2642** | Main class. See below. |
| `__main__` block | 2645-2698 | A self-demo with `Console(record=True)`. |

## `class Console` — public surface

All methods below are on `Console` unless noted. *Lines* are from the
reference implementation; a rebuild may reorder freely.

### Construction / properties
| Method | Lines | Purpose |
|---|---|---|
| `__init__(self, *, color_system="auto", force_terminal=None, force_jupyter=None, force_interactive=None, soft_wrap=False, theme=None, stderr=False, file=None, quiet=False, width=None, height=None, style=None, no_color=None, tab_size=8, record=False, markup=True, emoji=True, emoji_variant=None, highlight=True, log_time=True, log_path=True, log_time_format="[%X]", highlighter=ReprHighlighter(), legacy_windows=None, safe_box=True, get_datetime=None, get_time=None, _environ=None)` | 619-751 | Heavy validation: jupyter cols/lines, COLUMNS/LINES env, color-system detection, lock, theme stack init. |
| `__repr__` | 753-754 | `<console width=... ColorSystem>`. |
| `file` getter/setter | 756-768 | Defaults to sys.stderr if `stderr=True`, else sys.stdout. Falls back to `NULL_FILE` if file is None. |
| `_buffer` / `_buffer_index` / `_theme_stack` | 770-787 | Thread-local bridges. |

### Capability detection
| Method | Lines | Purpose |
|---|---|---|
| `_detect_color_system()` | 789-811 | Returns `Optional[ColorSystem]`. |
| `color_system` (property) | 908-919 | Returns `Optional[str]` of the system name. |
| `encoding` (property) | 921-928 | `file.encoding` lowercased, default utf-8. |
| `is_terminal` (property) | 930-976 | Honors `_force_terminal`, IDLE, Jupyter, `TTY_COMPATIBLE`, `FORCE_COLOR`, `isatty()`. |
| `is_dumb_terminal` (property) | 978-988 | True when `TERM ∈ {"dumb","unknown"}` AND is_terminal. |
| `options` (property) | 990-1002 | Current `ConsoleOptions`. |
| `size` (getter/setter) | 1004-1054 | `ConsoleDimensions`; uses `_STD_STREAMS_OUTPUT` on Windows, full `_STD_STREAMS` on POSIX; `COLUMNS`/`LINES` env override. |
| `width` / `height` (getter/setter) | 1056-1090 | |
| `bell()` | 1092-1094 | `Control.bell()` via `self.control()`. |

### Output primitives
| Method | Lines | Purpose |
|---|---|---|
| `capture()` → `Capture` | 1096-1111 | CM; disables file writes. |
| `pager(pager=None, styles=False, links=False)` | 1113-1134 | CM; strips links/styles per flags. |
| `line(count=1)` | 1136-1144 | Prints blank lines. |
| `clear(home=True)` | 1146-1155 | `Control.clear()` (+optional `home`). |
| `status(status, *, spinner="dots", spinner_style="status.spinner", speed=1.0, refresh_per_second=12.5)` | 1157-1188 | Returns a `Status` CM. |
| `show_cursor(show=True) -> bool` | 1190-1199 | No-op when not is_terminal. |
| `set_alt_screen(enable=True) -> bool` | 1201-1220 | No-op when not is_terminal or legacy Windows. |
| `is_alt_screen` (property) | 1222-1229 | |
| `set_window_title(title) -> bool` | 1231-1261 | |
| `screen(hide_cursor=True, style=None)` | 1263-1275 | CM. |

### Render pipeline
| Method | Lines | Purpose |
|---|---|---|
| `measure(renderable, *, options=None) -> Measurement` | 1277-1292 | |
| `render(renderable, options=None) -> Iterable[Segment]` | 1294-1343 | Recurses on nested renderables; raises `NotRenderableError`. |
| `render_lines(renderable, options=None, *, style=None, pad=True, new_lines=False) -> List[List[Segment]]` | 1345-1407 | Pads to fill `render_height` if set. |
| `render_str(text, *, style="", justify=None, overflow=None, emoji=None, markup=None, highlight=None, highlighter=None) -> Text` | 1409-1468 | Converts str → Text with optional emoji/markup/highlight. |

### Style / hooks
| Method | Lines | Purpose |
|---|---|---|
| `get_style(name, *, default=None) -> Style` | 1470-1498 | Resolves by name or parses; `MissingStyle` if unparseable and no default. |
| `_collect_renderables(objects, sep, end, *, justify=None, emoji=None, markup=None, highlight=None) -> List[ConsoleRenderable]` | 1500-1587 | Joins strings with sep, wraps in Align if justify; routes unknowns through Pretty. |

### Print / log / rule
| Method | Lines | Purpose |
|---|---|---|
| `rule(title="", *, characters="─", style="rule.line", align="center")` | 1589-1608 | |
| `control(*control: Control)` | 1610-1618 | Skipped on dumb-terminal. |
| `out(*objects, sep=" ", end="\n", style=None, highlight=None)` | 1620-1650 | Low-level: no pretty, no wrap, no markup, no crop. |
| `print(*objects, sep=" ", end="\n", style=None, justify=None, overflow=None, no_wrap=None, emoji=None, markup=None, highlight=None, width=None, height=None, crop=True, soft_wrap=None, new_line_start=False)` | 1652-1756 | Main writing entry. Applies render hooks, renders, applies style, splits/crops, pushes to buffer. |
| `print_json(json=None, *, data=None, indent=2, highlight=True, skip_keys=False, ensure_ascii=False, check_circular=True, allow_nan=True, default=None, sort_keys=False)` | 1758-1817 | Wraps `rich.json.JSON` and prints with soft_wrap. |
| `update_screen(renderable, *, region=None, options=None)` | 1819-1851 | Raises `NoAltScreen` otherwise. |
| `update_screen_lines(lines, x=0, y=0)` | 1853-1871 | |
| `print_exception(*, width=100, extra_lines=3, theme=None, word_wrap=False, show_locals=False, suppress=(), max_frames=100)` | 1873-1906 | |
| `_caller_frame_info(offset, currentframe=None)` | 1908-1945 | Static; walks `frame.f_back` `offset+1` times. |
| `log(*objects, sep=" ", end="\n", style=None, justify=None, emoji=None, markup=None, highlight=None, log_locals=False, _stack_offset=1)` | 1947-2028 | Decorates with `_log_render` (time+path:line). |

### Capture / live / hook plumbing
| Method | Lines | Purpose |
|---|---|---|
| `on_broken_pipe()` | 2030-2042 | Sets quiet, redirects stdout to devnull, `raise SystemExit(1)`. |
| `_check_buffer()` | 2044-2057 | Renders if `not quiet`; converts BrokenPipeError. |
| `_write_buffer()` | 2059-2130 | Honors `record`; legacy-Windows uses `LegacyWindowsTerm`; non-std modern streams chunk-write 32 KB; Jupyter uses `from .jupyter import display`. |
| `_render_buffer(buffer)` | 2132-2154 | Respects `no_color`; skips control when not is_terminal. |
| `input(prompt="", *, markup=True, emoji=True, password=False, stream=None) -> str` | 2156-2190 | Wraps `input()` / `getpass.getpass`. |

### Exporters (require `record=True`)
| Method | Lines | Purpose |
|---|---|---|
| `export_text(*, clear=True, styles=False)` | 2192-2222 | Plain or ANSI-flavored text from `_record_buffer`. |
| `save_text(path, *, clear=True, styles=False)` | 2224-2242 | |
| `export_html(*, theme=None, clear=True, code_format=None, inline_styles=False)` | 2244-2319 | Iterates `Segment.filter_control(Segment.simplify(...))`; constructs `<span>/<a>` and a `.rN{}` stylesheet. |
| `save_html(path, *, theme=None, clear=True, code_format=CONSOLE_HTML_FORMAT, inline_styles=False)` | 2321-2350 | |
| `export_svg(*, title="Rich", theme=None, clear=True, code_format=CONSOLE_SVG_FORMAT, font_aspect_ratio=0.61, unique_id=None)` | 2352-2604 | Builds an SVG from segment runs; uses `zlib.compress` for coordinate streams; reads `_theme.foreground_color.hex` and `_theme.background_color.hex`; the `unique_id` defaults to a content hash. |
| `save_svg(path, *, ...)` | 2606-2642 | Wraps `open(path, "w", encoding="utf-8").write(svg)`. |

### `__main__` demo
| Lines | Purpose |
|---|---|
| 2645-2698 | Constructs `Console(record=True)`, calls `log()` then `print()` with structured data. Exists for sanity, not as a public API.

## Tests mapping (`tests/test_console.py`)

| Source area | Test functions |
|---|---|
| Color/Jupyter detection | `test_dumb_terminal`, `test_soft_wrap`, `test_16color_terminal`, `test_truecolor_terminal`, `test_kitty_terminal` |
| `ConsoleOptions` | `test_console_options_update`, `test_console_options_update_height` |
| Init / size / repr | `test_init`, `test_size`, `test_size_can_fall_back_to_std_descriptors`, `test_repr` |
| Print / Json | `test_print`, `test_print_empty_with_end`, `test_print_multiple`, `test_print_text`, `test_print_text_multiple`, `test_print_json`, `test_print_json_error`, `test_print_json_data`, `test_print_json_ensure_ascii`, `test_print_json_with_default_ensure_ascii`, `test_print_json_indent_none`, `test_console_null_file` |
| Log | `test_log`, `test_log_milliseconds` |
| Capture / record / export | (later functions in same file) |
