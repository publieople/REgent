# Architecture (arc42-lite)

## 1. Goals

- Tiny Python package exposing a greeting API and matching CLI.
- Strict separation: API logic (`core`) is independent from output
  formatting (`formats`).
- Provide a clean test suite so the contract is enforceable on rebuild.

## 2. Quality goals / non-functional constraints

- Python ≥ 3.10 (uses `from __future__ import annotations`, PEP 604-ish).
- Build via PEP 517 / setuptools.
- Console-script entry point registered in `pyproject.toml`.
- All edge cases (empty / whitespace name) raise `ValueError`.
- Test framework: pytest. Suite lives in `tests/`.

## 3. Building blocks

```
greeter (package facade, src/greeter/__init__.py)
├── core   (greet, shout_greet)         depends on formats
├── formats (format_default, format_with_lang)
└── cli    (argparse + SystemExit)      depends on core
```

Data flow for `greet(name, lang='en')`:

```
cli.main(argv)
  → core.greet(name, lang)
      → formats.format_default(name)        if lang == "en"
      → formats.format_with_lang(name, lang) otherwise
```

`shout_greet` is `greet(...).upper()` — no separate logic.

CLI returns exit code `0` on success, `2` on `ValueError`.
