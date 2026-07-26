# Test oracle — greeter (white-box per-function)

The load-bearing subset of `tests/test_greeter.py`. One entry per public
symbol, distilled — not transcribed. Each entry pins ONE invariant the
rebuild's own test set might miss.

Source test fixture file: `tests/test_greeter.py` (8 cases).

### `greet(name, lang="en")`

- input: `""`
- expects: raises `ValueError("name must not be empty")`
- pins: empty-name path goes through validation, not format function;
  message is byte-exact.

### `greet(name, lang="en")`

- input: `"   "` (3 spaces)
- expects: raises `ValueError("name must not be empty")`
- pins: whitespace-only name is rejected — the strip happens AFTER the
  emptiness check, not before. Naive rebuilds strip first and accept
  `"   "`.

### `greet(name, lang="en")`

- input: `"  Ada  "` (surrounding whitespace)
- expects: returns `"Hello, Ada!"`
- pins: leading/trailing whitespace is silently stripped; result is the
  same as for `"Ada"`.

### `greet(name, lang="es")`

- input: `"Ada"`
- expects: returns `"Hola, Ada!"`
- pins: Spanish output uses half-width `,` and `!` (NOT the wide
  punctuation used by Chinese — easy to confuse).

### `greet(name, lang="zh")`

- input: `"Ada"`
- expects: returns `"你好，Ada！"` (full-width `，` and `！`)
- pins: Chinese output uses full-width comma `，` and full-width `！`.
  Half-width punctuation here is wrong.

### `greet(name, lang="xx")` (unknown language)

- input: `"Ada"`
- expects: returns `"Hello, Ada!"`
- pins: unknown lang falls back to English default — does NOT raise.

### `shout_greet(name, lang="en")`

- input: `"Ada"`
- expects: returns `"HELLO, ADA!"`
- pins: `shout_greet` is `greet(...).upper()`, NOT a separate
  formatter. Order matters — `shout_greet("Ada", "es")` must produce
  `"HOLA, ADA!"` (uppercase applied to the localized string, not
  before localization).

### `cli.main(argv=[""])` (CLI error path)

- input: argv is `[""]`, i.e. an empty name via the CLI
- expects: prints `"error: name must not be empty\n"` to **stderr**,
  returns exit code `2`, prints nothing to stdout
- pins: error prefix is literal `"error: "` (with space); message goes
  to stderr not stdout; exit code is `2` not `1`. Naive rebuilds
  print to stdout or exit `1`.

### `cli.main(argv=["--help"])`

- input: argv is `["--help"]`
- expects: argparse prints usage to stdout, returns exit code `0`
- pins: this is the standard argparse path; caught here so a rebuild
  that overrode argparse behavior would be flagged.

### `format_default(name)`

- input: `"O'Brien"`
- expects: returns `"Hello, O'Brien!"`
- pins: does NOT escape the apostrophe — passes through as-is.
  A rebuild that ran `escape(name)` to "be safe" would fail here.
