# greeter (package spec)

## Purpose

A Python package that builds greeting strings with optional localization
(English / Spanish / French / Chinese) and an optional uppercase mode.
Exposes both a Python API and a CLI.

## Requirements

### R1 — Public API

- MUST export `greet(name: str, lang: str = "en") -> str`.
- MUST export `shout_greet(name: str, lang: str = "en") -> str`.
- MUST export `format_default(name: str) -> str`.
- MUST export `format_with_lang(name: str, lang: str) -> str`.
- MUST expose `__version__ = "0.1.0"`.

### R2 — Behaviour

- SHOULD call `format_default` when `lang == "en"`.
- MUST delegate to `format_with_lang` for any other language.
- MUST strip leading/trailing whitespace from `name`.
- MUST raise `ValueError("name must not be empty")` for empty or
  whitespace-only names.
- `shout_greet` MUST equal `greet(...).upper()`.

### R3 — CLI

- MUST register a console script `greeter` mapping to `greeter.cli:main`.
- The CLI MUST accept positional `name`.
- The CLI MUST accept `--lang {en,es,fr,zh}` with default `en`.
- The CLI MUST accept `--shout` flag.
- The CLI MUST exit `0` on success, `2` on `ValueError`.
- When `ValueError` is caught, the CLI MUST print `error: <message>` to
  stderr (literal `"error: "` prefix, no other prefix is acceptable).

### R4 — Format strings (literal table)

`format_default` and `format_with_lang` MUST emit exactly these strings
(byte-for-byte, including punctuation):

| `lang` | output                       |
|--------|------------------------------|
| en     | `"Hello, {name}!"`           |
| es     | `"Hola, {name}!"`            |
| fr     | `"Bonjour, {name}!"`         |
| zh     | `"你好，{name}！"` (full-width `，` and `！`) |
| other  | falls back to `format_default` |

`name` is substituted into `{name}` only after whitespace has been stripped
of the surrounding input (per R2).

## Scenarios

### S1 — Default English greeting

WHEN `greet("Ada")` is called
THEN the return value is `"Hello, Ada!"`.

### S2 — Localized greeting

WHEN `greet("Ada", lang="es")` is called
THEN the return value is `"Hola, Ada!"`.

### S3 — Unknown language falls back

WHEN `greet("Ada", lang="xx")` is called
THEN the return value is `"Hello, Ada!"`.

### S4 — Empty name rejected

WHEN `greet("")` is called
THEN a `ValueError` is raised.

### S5 — Whitespace-only name rejected

WHEN `greet("   ")` is called
THEN a `ValueError` is raised.

### S6 — Whitespace stripped

WHEN `greet("  Ada  ")` is called
THEN the return value is `"Hello, Ada!"`.

### S7 — Shout

WHEN `shout_greet("Ada")` is called
THEN the return value is `"HELLO, ADA!"`.

### S8 — CLI happy path

WHEN `greeter Ada --lang es` is invoked
THEN stdout is `Hola, Ada!\n` and the exit code is `0`.

### S9 — CLI error path

WHEN `greeter ""` is invoked
THEN stderr contains `name must not be empty` and the exit code is `2`.
