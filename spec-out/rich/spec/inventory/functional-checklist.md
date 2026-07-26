# Functional checklist — `rich.console`

Each line is a single user-observable behavior with its verification.
A rebuild is graded by how many `- [ ]` become `- [x]`. Source line refs
(`console.py:L`) tell where in the original each lives.

## Construction & capability

- [ ] `Console()` with no args constructs and `repr` includes width + color system name (`console.py:753`).
- [ ] `Console(width=80, height=24)` overrides autodetect (`console.py:684-695`).
- [ ] `Console(file=io.StringIO()).file.write` receives all output to the buffer (`console.py:756-763`).
- [ ] `Console(quiet=True).print("x")` discards the buffer without writing (`console.py:2050-2052`).
- [ ] `Console(record=True)` populates `_record_buffer` whenever output is flushed (`console.py:2062-2065`).
- [ ] `Console(color_system="truecolor").color_system == "truecolor"` (`console.py:909-919`).
- [ ] `force_terminal=True` on a non-TTY file emits ANSI (`console.py:939-940`).
- [ ] `NO_COLOR=1` env ⇒ `console.no_color` is True; output has no color (`console.py:725-729`, `2139`).
- [ ] `TERM=dumb` and `is_terminal=True` ⇒ `is_dumb_terminal=True`; `control()` is no-op (`console.py:978-988`, `1616`).
- [ ] `isatty()` raising ValueError (closed stream) returns False (`console.py:971-976`).
- [ ] `JUPYTER_COLUMNS="200"` env in Jupyter sets `width=200` (`console.py:660-664`).
- [ ] Idle's `sys.stdin.__module__=="idlelib.X"` ⇒ `is_terminal=False` (`console.py:942-947`).

## Options

- [ ] `ConsoleOptions(...).copy()` is a distinct instance with same values (`console.py:147-155`).
- [ ] `options.update(width=10).min_width == options.update(width=10).max_width == 10` (`console.py:172-174`).
- [ ] `options.update(width=NO_CHANGE)` leaves width unchanged (`console.py:172`).
- [ ] `ascii_only` property returns `not encoding.startswith("utf")` (`console.py:142-145`).

## Buffer / threading

- [ ] Nested `with console:` blocks: outer flush only when the innermost exits (`console.py:2067`).
- [ ] `_buffer_index` is per-thread (use a fresh thread to confirm isolation; original keeps buffer on `threading.local`, lines 535-541).

## Render pipeline

- [ ] `console.print("hello")` on a non-TTY file writes the string `hello\n` (`console.py:1652-1756`).
- [ ] `console.print("[bold]X[/]")` on a terminal emits `X` with bold ANSI (`console.py:1409-1468`).
- [ ] `console.print(123)` invokes `highlighter` and renders a Text (`console.py:1578-1579`).
- [ ] `console.print({"a":1})` routes through `pretty.Pretty` (`console.py:1573-1577`).
- [ ] `console.render(invalid_obj)` raises `rich.errors.NotRenderableError` with the documented message (`console.py:1325-1329`).
- [ ] `console.render(class_obj)` does NOT treat the class as renderable (`console.py:1318`).
- [ ] `console.render_lines(r, options=options.update(height=10))` returns at most 10 lines, padded with spaces if shorter (`console.py:1375-1406`).

## Output primitives

- [ ] `console.line(3)` writes 3 newlines (`console.py:1136-1144`).
- [ ] `console.clear()` with `home=True` emits `Control.clear()`+`Control.home()` (`console.py:1146-1155`).
- [ ] `console.bell()` writes the bell control code (`console.py:1092-1094`).
- [ ] `console.rule("Title")` draws a horizontal rule with centered title (`console.py:1589-1608`).
- [ ] `console.out("a", "b")` joins with `" "` and never wraps or pretty-prints (`console.py:1620-1650`).
- [ ] `console.print(..., soft_wrap=True)` implies `no_wrap=True, overflow="ignore", crop=False` (`console.py:1697-1702`).
- [ ] `console.print(..., new_line_start=True, "...line1\nline2")` prepends `Segment.line()` (`console.py:1743-1748`).
- [ ] `console.print_json(data={"a":1})` emits valid JSON parseable by `json.loads` (`console.py:1758-1817`).
- [ ] `console.print_json(json=42)` raises `TypeError` with the documented message (`console.py:1802-1805`).
- [ ] `console.print_exception()` runs (smoke test; assert no traceback emitted to stderr) (`console.py:1873-1906`).
- [ ] `console.log("x")` prepends a `[HH:MM:SS]` time and the caller's filename:line (`console.py:1947-2028`).
- [ ] `console.log("x", log_locals=True)` includes a `[i]locals` block (`console.py:1996-2004`).

## Capture / record / export

- [ ] `with console.capture() as c: console.print("z"); s = c.get()` ⇒ `s == "z\n"` (`console.py:310-340`).
- [ ] `capture.get()` before `__exit__` raises `CaptureError` (`console.py:336-339`).
- [ ] `console.export_text()` without `record=True` raises AssertionError with the exact message (`console.py:2204-2206`).
- [ ] `console.export_text()` with `record=True` returns concatenated plain text (`console.py:2209-2221`).
- [ ] `console.save_text("/tmp/x.txt")` writes a UTF-8 file (`console.py:2224-2242`).
- [ ] `console.export_html()` returns a string containing `<style>` (or inline `style="..."` if `inline_styles=True`) (`console.py:2264-2319`).
- [ ] `console.export_svg()` returns a string starting with `<svg` (`console.py:2352-2604`).
- [ ] `console.save_html("/tmp/x.html")`, `console.save_svg("/tmp/x.svg")` write UTF-8 (`console.py:2321-2350`, `2606-2642`).

## Context managers

- [ ] `with console.screen():` enables alt screen on enter, disables on exit; cursor hidden if requested (`console.py:403-447`).
- [ ] `with console.pager():` calls `pager.show(...)` on clean exit (`console.py:364-400`).
- [ ] `with console.use_theme(t):` pushes/pops the theme stack (`console.py:343-361`).
- [ ] `console.update_screen(...)` outside alt screen raises `NoAltScreen` (`console.py:1819-1851`).
- [ ] `console.set_alt_screen(True)` then `False` returns True both times on a terminal (`console.py:1201-1220`).
- [ ] `console.show_cursor(True)` on a non-terminal returns False and writes nothing (`console.py:1190-1199`).

## Errors / broken pipe

- [ ] Piping to `head -1` (or equivalent) of a printing program triggers `on_broken_pipe`; `SystemExit(1)` raised; `sys.stdout.fileno()` is now a dup of `/dev/null` (`console.py:2030-2042`).
- [ ] `get_style("not a [valid style")` raises `MissingStyle("Failed to get style 'not a [valid style'; ...")` (`console.py:1492-1497`).
- [ ] `get_style(..., default="bold")` returns the default Style on parse failure (`console.py:1494-1495`).

## stdin

- [ ] `console.input(prompt="> ")` writes prompt (using `print`, so styled if markup), then calls `input()` / `getpass` as configured (`console.py:2156-2190`).
- [ ] `console.input(..., password=True)` reads via `getpass.getpass("", stream=stream)` (`console.py:2181-2184`).

## Protocols (duck-typed, sanity checks)

- [ ] An object with `__rich_console__(console, options)` is rendered via `Console.render` (`console.py:1318-1319`).
- [ ] An object with `__rich__()` returning a renderable is dispatched through `rich_cast` (`console.py:1317`).
- [ ] `RichCast` and `ConsoleRenderable` are `isinstance` checkable (via `@runtime_checkable`, lines 246-263).
