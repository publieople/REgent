# conventions/architecture-rules.md

The rules v0.2.0 demands for any scanned repo, applied to `crates/regex`.

## A. Lazy imports (skill v0.2.0)

**Finding: none in `crates/regex`.**

```
$ grep -rn '^\s*use ' crates/regex/src/*.rs
crates/regex/src/error.rs:71:    use bstr::ByteSlice;   // inside Display impl
```

The only `use` inside a function body is `crates/regex/src/error.rs:71`,
which is a deliberate import inside `Display for Error` to keep the
`ByteSlice` trait in scope for the format strings. This is **not** a
platform-gated lazy import — it is a style choice (avoid `use` at module
top for a one-off trait method).

**Action for rebuild:** mirror this pattern. Do not move the `use` to the
top of `error.rs`.

## B. Trait (Protocol/ABC) contracts

The skill v0.2.0 says: *"For every `Protocol` / `ABC` declared in the
scanned source, list every abstract / duck-typed method in the spec's
`R-` section, with the caller dispatch site."*

The Rust equivalent of a Protocol is a `trait`. The Rust equivalent of an
abstract method is a trait method **without a default body**. ripgrep has:

### `grep_matcher::Matcher` (crates/matcher/src/lib.rs:373)

| Required method | Caller dispatch site |
|---|---|
| `type Captures: Captures` | set by each impl, e.g. `RegexMatcher: Captures = RegexCaptures` at `matcher.rs:410` |
| `type Error: std::fmt::Display` | `RegexMatcher: Error = NoError` at `matcher.rs:411` |
| `fn find_at(&self, &[u8], usize) -> Result<Option<Match>, Self::Error>` | called by `Matcher::find`, `try_find_iter_at`, `shortest_match_at` (defaults) |
| `fn new_captures(&self) -> Result<Self::Captures, Self::Error>` | called by `Matcher::captures` (default) |

There is **no `#[dyn-compatible]` / "object-safe" annotation in Rust 1.96**
(`dyn Matcher` is implicitly supported because none of the required
methods use `Self` in argument position other than via `&self`).

### `grep_matcher::Captures` (crates/matcher/src/lib.rs:263)

| Required method | Caller dispatch site |
|---|---|
| `fn len(&self) -> usize` | used by `Captures::is_empty` (default) |
| `fn get(&self, usize) -> Option<Match>` | used by `Captures::as_match` (default), by `Matcher::try_captures_iter_at` (default) |

### `std::error::Error` (impl on `Error` at `crates/regex/src/error.rs:67`)

| Required method | Override? |
|---|---|
| `fn source(&self) -> Option<&(dyn Error + 'static)>` | No (uses default → `None`) |

### `Default` (impl on `Config` at `crates/regex/src/config.rs:45`)

| Required method | Caller dispatch site |
|---|---|
| `fn default() -> Self` | called by `RegexMatcherBuilder::default` (`matcher.rs:28`) |

These four trait contracts are recorded as `R1`-`R4`, `R20`-`R22` in
`specs/regex.spec.md`.

## C. Files that own I/O (skill v0.2.0)

**Finding: `crates/regex` has NO I/O.** No `std::fs`, `std::io::Write`,
`std::process::exit`, no `println!`. The crate is pure: it takes a
pattern + bytes, returns matches or compile errors.

By contrast, the I/O is owned by:

| Module | I/O surface | Lines |
|---|---|---|
| `crates/core/main.rs` | `std::io::Write`, `process::ExitCode`, `ignore::WalkState` | line 5, line 9 |
| `crates/printer/src/**` | `std::io::Write`, color writes to stderr | (out of scope) |

The rebuild of `crates/regex` therefore **does not** need to record
`SystemExit` paths, `os.dup2`, or broken-pipe handling. Those are in
scope for any rebuild that touches `crates/core`.

## D. `#[cfg(...)]` platform branches (skill v0.2.0 analog)

| File:line | Cfg | Effect |
|---|---|---|
| `crates/core/main.rs:60-62` | `cfg(all(target_env = "musl", target_pointer_width = "64"))` | jemalloc global allocator |
| `crates/regex/src/ast.rs:18` | `cfg(test)` | module-level inline tests |
| `crates/regex/src/ast.rs:146` | `cfg(test)` | test helper module |
| `crates/regex/src/ban.rs:55` | `cfg(test)` | inline tests |
| `crates/regex/src/literal.rs:641` | `cfg(test)` | inline tests |
| `crates/regex/src/matcher.rs:553` | `cfg(test)` | inline tests (6 `#[test]`) |
| `crates/regex/src/strip.rs:121` | `cfg(test)` | inline tests |
| `crates/regex/src/non_matching.rs:83` | `cfg(test)` | inline tests |

**No `cfg(unix)` / `cfg(windows)` / `cfg(target_os = ...)` platform
gates inside `crates/regex`** — the crate is fully cross-platform and
does no I/O. (Those gates exist in `crates/searcher/src/searcher/mmap.rs`
and `crates/ignore/src/dir.rs`, out of scope.)

## E. `#[derive(...)]` macros (skill v0.2.0 analog)

`#[derive]` is the Rust analog of Python dataclasses. Treat each derive
as a public contract on the type.

| Type | Derives | File:line |
|---|---|---|
| `RegexMatcherBuilder` | `Clone, Debug` | `crates/regex/src/matcher.rs:23` |
| `RegexMatcher` | `Clone, Debug` | `crates/regex/src/matcher.rs:366` |
| `RegexCaptures` | `Clone, Debug` | `crates/regex/src/matcher.rs:523` |
| `Config` | `Clone, Debug` | `crates/regex/src/config.rs:24` |
| `ConfiguredHIR` | `Clone, Debug` | `crates/regex/src/config.rs:157` |
| `Error` | `Clone, Debug` | `crates/regex/src/error.rs:6` |
| `ErrorKind` | `Clone, Debug` | `crates/regex/src/error.rs:40` (`#[non_exhaustive]` adds a stability promise — adding variants is non-breaking) |
| `AstAnalysis` | `Clone, Debug` | `crates/regex/src/ast.rs:5` |
| `InnerLiterals` | `Clone, Debug` | `crates/regex/src/literal.rs:39` |
| `TSeq` | `Clone, Debug` | `crates/regex/src/literal.rs:439` |
| `Extractor` | `Debug` only | `crates/regex/src/literal.rs:130` |

**`#[non_exhaustive]` on `ErrorKind`** is a stability contract:
adding new variants later is non-breaking. A rebuild that drops this
attribute would be a breaking change.

## F. Cargo features (skill v0.2.0 analog)

The `pcre2` feature at `Cargo.toml:69-71` is the **only** opt-in
Cargo feature in the workspace.

```
[features]
pcre2 = ["grep/pcre2"]
```

It is OFF by default. Turning it on via `cargo build --features pcre2`
flips a transitive feature on the `grep` facade crate, which adds
`pcre2-sys` (a C library binding) as a dependency. The regex engine
itself has no `Cargo.toml [features]` section — it is built identically
with or without `pcre2`.

**Action for rebuild:** `crates/regex/Cargo.toml` should have NO
`[features]` table. The `pcre2` feature is exposed only at the
workspace root.

## G. `panic!` / unreachable behavior

- `grep_matcher::NoError::Display` panics with message
  `"BUG for NoError: an impossible error occurred"` (line ~342 of
  `crates/matcher/src/lib.rs`). This is acceptable because the type
  exists only for matchers that cannot fail; if it ever fires, the
  program is in an unrecoverable state.
- No `unwrap()` on user input in the regex engine (verified by
  `grep -n 'unwrap()' crates/regex/src/matcher.rs` — only `matcher.rs`
  uses unwrap and only on internally-built state).