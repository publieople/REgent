# Functional checklist

The rebuild is verified against this list. Each entry is a concrete,
command- or call-shaped check that the rebuilt package must satisfy.

## API behaviour

- [ ] `greet("Ada")` returns `"Hello, Ada!"`.
- [ ] `greet("Ada", "es")` returns `"Hola, Ada!"`.
- [ ] `greet("Ada", "fr")` returns `"Bonjour, Ada!"`.
- [ ] `greet("Ada", "zh")` returns `"你好，Ada！"`.
- [ ] `greet("Ada", "xx")` returns `"Hello, Ada!"` (fallback).
- [ ] `greet("  Ada  ")` returns `"Hello, Ada!"` (whitespace stripped).
- [ ] `greet("")` raises `ValueError`.
- [ ] `greet("   ")` raises `ValueError`.
- [ ] `shout_greet("Ada")` returns `"HELLO, ADA!"`.
- [ ] `shout_greet("Ada", "es")` returns `"HOLA, ADA!"`.

## CLI behaviour

- [ ] `greeter Ada` prints `Hello, Ada!` and exits `0`.
- [ ] `greeter Ada --lang es` prints `Hola, Ada!` and exits `0`.
- [ ] `greeter Ada --shout` prints `HELLO, ADA!` and exits `0`.
- [ ] `greeter ""` prints an error to stderr and exits `2`.
- [ ] `greeter --help` exits `0` and prints usage.

## Test suite

- [ ] `pytest` from the rebuilt project root exits `0`.
- [ ] Pytest discovers **at least 8** test cases (matches
      `tests/test_greeter.py`).
- [ ] Every test in the rebuilt suite mirrors the 8 scenarios in
      `specs/greeter.spec.md`.

## Package metadata

- [ ] `import greeter; greeter.__version__ == "0.1.0"`.
- [ ] `pip install -e .` from the rebuilt root registers a `greeter`
      console script that maps to `greeter.cli:main`.

## Pass criterion

The rebuild is accepted when **every box above is checked**.
