# conventions/code-style.md

Every rule below cites a file and line. If a rebuild agent cannot locate
the cited line, the rule is wrong.

## 1. Edition & formatter

- **Edition 2024** is mandatory.
  - Source: `crates/regex/Cargo.toml:14` (`edition = "2024"`).
  - Source: `rustfmt.toml:3` (`edition = "2024"`).
- **`rustfmt.toml` lives at the workspace root.**
  - `max_width = 79` — every line ≤ 79 chars (line 1).
  - `use_small_heuristics = "max"` — preserves small-line heuristic (line 2).
  - These settings match `rust-lang/rust`'s style.
- **No formatter inside individual crates.** Style is enforced at the
  workspace root, not per-crate.

## 2. Lints

- `#![deny(missing_docs)]` is present at the crate level for
  `crates/regex` (`crates/regex/src/lib.rs:3`) and `crates/matcher`
  (`crates/matcher/src/lib.rs:40`).
- No `clippy.toml` exists at the workspace root, so default `clippy` lints
  apply. A rebuild agent SHOULD run `cargo clippy --all-targets` but is
  not required to fix warnings unrelated to the spec.

## 3. Imports

- **Grouped `use {}` blocks at the top of every file.** All external
  imports come first, then a blank line, then crate-local imports.
  - Example: `crates/regex/src/matcher.rs:1-12`.
- **No `use std::…::…;` one-per-line.** Use the brace form:
  `use std::{io::Write, process::ExitCode};`
  - Example: `crates/core/main.rs:5`.
- **Aliased imports for trait-method disambiguation.** The matcher module
  renames `regex_automata::util::captures::Captures` to `AutomataCaptures`
  to avoid collision with `grep_matcher::Captures`:
  - `crates/regex/src/matcher.rs:5-9`.
- **No `use` inside function bodies** in this crate (verified by
  `grep -n '^\s*use ' crates/regex/src/*.rs` — only `error.rs:71` has
  one, a deliberate `use bstr::ByteSlice;` inside `Display for Error`).
  v0.2.0's "lazy-import note" therefore has **nothing to record** for the
  regex engine (no Platform-Cfg-gated imports either).

## 4. Naming

- Types / traits: `PascalCase`.
  - Examples: `RegexMatcher`, `RegexMatcherBuilder`, `ConfiguredHIR`,
    `LineTerminator`, `Captures`.
- Methods / fields: `snake_case`.
  - Examples: `case_insensitive`, `swap_greed`, `find_at`,
    `non_matching_bytes`.
- Builder flags: same as the underlying config field, e.g.
  `RegexMatcherBuilder::case_insensitive(bool) -> &mut Self`
  sets `Config::case_insensitive`.

## 5. Type signatures

- **Builder methods return `&mut Self`** so they can be chained. This is
  the convention used throughout `crates/regex/src/matcher.rs:99-360`.
  A rebuild that returns `Self` instead would break the call sites.
- **Public methods that can fail return `Result<T, Error>`.** The error
  type is always the crate-local `Error` (not `anyhow::Error` or
  `Box<dyn std::error::Error>`).
  - Source: `crates/regex/src/matcher.rs:45` (`Result<RegexMatcher, Error>`).
- **Methods that can't fail return `Result<T, NoError>`.** This lets the
  trait object be plugged into APIs that require a `Result`-returning
  matcher.
  - Source: `crates/regex/src/matcher.rs:418` (`Result<Option<Match>, NoError>`).
- **No `unsafe` in this crate** (verified by `grep -rn 'unsafe' crates/regex/src/`).

## 6. Comments / docs

- Every public item has a doc comment (`///`). Enforced by
  `#![deny(missing_docs)]` and verified by `cargo doc` succeeding.
- Line comments (`//`) are used for in-flow rationale, e.g.
  `crates/core/main.rs:25-50` explains why jemalloc is conditional.
- Module-level docs are written as `/*! ... */` (e.g. `crates/regex/src/lib.rs:1-9`).

## 7. Tests

- Inline `#[cfg(test)] mod tests { ... }` blocks at the bottom of each
  source file. Six `#[test]` annotations in
  `crates/regex/src/matcher.rs:553-670`.
- Each test uses `assert!(matcher.is_match(b"…")?.unwrap())` style — no
  external test framework, no `#[should_panic]`, no fixture files for
  the regex engine (all haystacks are byte literals).
- Workspace-wide `cargo test` runs all 500+ `#[test]` annotations.
  Integration tests under `tests/` use `assert_cmd` to shell out to the
  `rg` binary.