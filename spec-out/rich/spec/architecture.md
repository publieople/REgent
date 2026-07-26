# Architecture — Rich Console

## Quality goals (in priority order)

1. **Thread safety.** Multiple threads must call `print`/`log`/`rule` and
   run context managers without corrupting the output stream.
2. **Correct ANSI / segment rendering.** A renderable that supports
   `__rich_console__(console, options)` must be dispatched correctly;
   strings must go through `render_str`; unknown objects must raise a
   `NotRenderableError` rather than silently emitting garbage.
3. **Environment-aware capability detection.** TTY, Jupyter, Windows VT,
   `NO_COLOR`, `FORCE_COLOR`, `TERM`, `COLORTERM`, `COLUMNS`, `LINES`,
   `TTY_COMPATIBLE`, `TTY_INTERACTIVE` must all be honored.
4. **Bufferable output.** All output goes through a thread-local segment
   buffer; only when buffer-index returns to 0 is text actually written to the
   underlying file.
5. **Recordable.** With `record=True`, the rendered segments are also
   mirrored to a separate buffer for HTML/SVG/text export.
6. **No global state besides thread-locals.** Two `Console` instances must
   not interfere.

## Building blocks

- **Protocols** — `RichCast.__rich__`, `ConsoleRenderable.__rich_console__`.
  Runtime-checkable via `@runtime_checkable`.
- **`ConsoleDimensions`** — NamedTuple of `(width: int, height: int)`. Cells/lines.
- **`ConsoleOptions`** — Immutable dataclass; updates return a copy. Holds
  `size`, `legacy_windows`, `min_width`, `max_width`, `is_terminal`,
  `encoding`, `max_height`, optional `justify/overflow/no_wrap/highlight/markup/height`.
  `ascii_only` is derived (`not encoding.startswith('utf')`).
- **`ConsoleThreadLocals`** — `threading.local` carrying per-thread
  `theme_stack: ThemeStack`, `buffer: list[Segment]`, `buffer_index: int`.
- **`RenderHook`** — ABC; one method `process_renderables(list) -> list`.
- **Public render context managers:** `Capture`, `ThemeContext`, `PagerContext`,
  `ScreenContext`.
- **Renderables defined here:** `NewLine`, `ScreenUpdate`, `Group`.

## Dataflow (per render-call to `print`/`log`/`rule`/etc.)

```
objects, sep, end, *, style, justify, ...
        │
        ▼
self._collect_renderables(...)  ──── joins strings with sep, wraps in
        │                              Align if justify ∈ {left,center,right},
        │                              routes non-renderables through Pretty
        ▼
for hook in self._render_hooks:     (push_render_hook / pop_render_hook stack)
    hook.process_renderables(renderables)
        │
        ▼
self.options.update(...)           (apply width/height/no_wrap/markup/...)
        │
        ▼
self.render(renderable, options)   ── dispatches to __rich_console__ or
        │                              render_str; recurses on nested renderables;
        │                              raises NotRenderableError otherwise
        ▼
Segment.split_lines_terminator /   (apply style if set; prepend Segment.line()
 Segment.split_and_crop_lines       if new_line_start and multi-line)
        │
        ▼
self._buffer.extend(...)           (per-thread; possibly nested)
        │
        ▼
_check_buffer()            (called on __exit__ / end_capture; no-op if quiet;
        │                   catches BrokenPipeError -> on_broken_pipe() -> SystemExit(1))
        ▼
_write_buffer()            (only when buffer_index == 0; honors record,
        │                   clears buffer after write; legacy-Windows branch
        │                   calls legacy_windows_render; non-std modern streams
        │                   chunk-write at 32 KB to avoid Windows 8K bug)
        ▼
file.write(text) + file.flush()
```

## Threading model

- One `threading.RLock` instance per `Console` (`_lock`). Used around buffer
  / live / render-hook stack mutation.
- `_record_buffer_lock` separate `RLock` for the record buffer.
- Each thread sees its own segment buffer via `ConsoleThreadLocals`.
- `_buffer_index` tracks nesting depth of buffer contexts per thread.
  `_write_buffer` only fires when the outermost thread-local buffer exits
  (`_buffer_index == 0`).

## Error / exit code contract

Rich is a library, not a CLI. Errors raised:

- `rich.errors.NotRenderableError` — `render()` cannot coerce.
- `rich.errors.NoAltScreen` — `update_screen` / `update_screen_lines`
  called outside alt-screen mode.
- `rich.errors.MissingStyle` — `get_style` cannot parse and no default given.
- `rich.errors.StyleSyntaxError` — bubbled from `Style.parse`.
- `rich.errors.LiveError` — `set_live` while another live is active.
- `CaptureError` (defined here) — `Capture.get()` called before `__exit__`.
- `TypeError` from `print_json` when `json=` is non-str.
- `BrokenPipeError` is converted to `SystemExit(1)` via `on_broken_pipe`
  (which also redirects stdout to devnull). Subclasses may override.

## Recording → export

`record=True` populates `_record_buffer` whenever `_write_buffer` runs at
`buffer_index == 0`. Exporters (`export_text`, `export_html`, `export_svg`)
all assert `self.record`, read `_record_buffer` under `_record_buffer_lock`,
and (unless `clear=False`) drain it on read. SVG additionally requires
`zlib` for compression of coordinate streams.
