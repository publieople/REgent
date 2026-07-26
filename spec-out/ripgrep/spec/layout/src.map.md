# src.map.md — file → purpose + public API

Only in-scope files. Every entry has a one-line purpose, public API, and
where its tests live. Line ranges use the original file numbering.

---

## `crates/matcher/src/lib.rs` — the trait

**Purpose:** the abstract `Matcher` interface every ripgrep search backend
implements. Defines `Match`, `Captures`, `LineTerminator`, `ByteSet`,
`LineMatchKind`, `NoCaptures`, `NoError`, and the central `Matcher` trait.

**Public API (lines = approximate, against `crates/matcher/src/lib.rs`):**

| Item                  | Line | Kind     | 1-line behavior                                    |
|-----------------------|------|----------|----------------------------------------------------|
| `Match`               | ~80  | struct   | `start <= end` byte range. `new`, `zero`, `offset` |
| `Match::with_start`   | ~110 | method   | Returns new match; panics if `start > self.end`    |
| `LineTerminator`      | ~150 | struct   | `Byte(u8)` or `CRLF`; default is `b'\n'`           |
| `LineTerminator::crlf`| ~163 | method   | Treats lone `\n` as a terminator too               |
| `ByteSet`             | ~205 | struct   | 256-bit bitset; `add`, `remove`, `contains`, `full`|
| `Captures` (trait)    | ~263 | trait    | `len`, `get`, `as_match`, `interpolate`            |
| `NoCaptures`          | ~310 | struct   | always-empty Captures impl                         |
| `NoError`             | ~326 | struct   | `Display` panics (impossible error)                |
| `LineMatchKind`       | ~354 | enum     | `Confirmed(usize)` / `Candidate(usize)`            |
| `Matcher` (trait)     | ~373 | trait    | required: `find_at`, `new_captures`                |
| `Matcher::find_at`    | ~410 | method   | REQUIRED — first match after `at`                  |
| `Matcher::new_captures` | ~426 | method | REQUIRED — empty capture group                     |
| `Matcher::try_find_iter_at` | ~504 | method | iter; callback returns `Result<bool, E>`         |
| `Matcher::captures_at`| ~614 | method   | populate captures; default returns `Ok(false)`     |
| `Matcher::non_matching_bytes` | ~676 | method | `Option<&ByteSet>`                        |
| `Matcher::line_terminator` | ~692 | method | `Option<LineTerminator>`                    |
| `Matcher::find_candidate_line` | ~736 | method | confirmed or candidate line              |
| `impl<M: Matcher> Matcher for &M` | ~766 | blanket | `&Matcher` is also a `Matcher`            |

**Required methods of `Matcher` (the contract):**
1. `type Captures: Captures`
2. `type Error: std::fmt::Display`
3. `fn find_at(&self, haystack: &[u8], at: usize) -> Result<Option<Match>, Self::Error>`
4. `fn new_captures(&self) -> Result<Self::Captures, Self::Error>`

All other methods have default implementations derived from these two.

**Tests:** `crates/matcher/tests/test_matcher.rs`, `crates/matcher/tests/tests.rs`,
`crates/matcher/tests/util.rs`.

---

## `crates/regex/src/lib.rs`

**Purpose:** re-export the public API of the `grep-regex` crate.

```rust
pub use crate::{
    error::{Error, ErrorKind},
    matcher::{RegexCaptures, RegexMatcher, RegexMatcherBuilder},
};
mod ast; mod ban; mod config; mod error; mod literal;
mod matcher; mod non_matching; mod strip;
```

No tests, no logic.

---

## `crates/regex/src/matcher.rs` — **the main surface**

**Purpose:** implements `grep_matcher::Matcher` on top of
`regex_automata::meta::Regex`, with a builder for configuration.

**Public API:**

| Item                         | Line | Kind     | 1-line behavior                                     |
|------------------------------|------|----------|-----------------------------------------------------|
| `RegexMatcherBuilder`        | 23   | struct   | Holds `Config`. Default via `RegexMatcherBuilder::new` |
| `RegexMatcherBuilder::new`   | 36   | fn       | Default config                                      |
| `RegexMatcherBuilder::build` | 45   | fn       | Build matcher for one pattern → `Result<RegexMatcher, Error>` |
| `RegexMatcherBuilder::build_many` | 53 | fn  | Build matcher for N patterns, joined as alternation  |
| `RegexMatcherBuilder::build_literals` | 92 | fn | Faster path for plain literal strings                |
| `RegexMatcherBuilder::case_insensitive` | 103 | method | `-i` flag                                       |
| `RegexMatcherBuilder::case_smart` | 120 | method | Smart-case (auto `-i` only when no uppercase literal) |
| `RegexMatcherBuilder::multi_line` | 131 | method | `-m` / multiline `^$`                              |
| `RegexMatcherBuilder::dot_matches_new_line` | 143 | method | `-s` / `s` flag                                  |
| `RegexMatcherBuilder::swap_greed` | 157 | method | `-U` / `U` flag                                   |
| `RegexMatcherBuilder::ignore_whitespace` | 167 | method | `-x` extended mode                                |
| `RegexMatcherBuilder::unicode` | 179 | method | `-u` flag (default ON)                            |
| `RegexMatcherBuilder::octal` | 199  | method   | Support `\0`-`\377` syntax (default OFF)            |
| `RegexMatcherBuilder::size_limit` | 209 | method | Approx bytes of compiled regex                     |
| `RegexMatcherBuilder::dfa_size_limit` | 223 | method | Per-thread DFA cache bytes                        |
| `RegexMatcherBuilder::nest_limit` | ~244 | method | Max AST depth                                     |
| `RegexMatcherBuilder::word`     | ~260 | method | `-w` flag — wrap in `\b … \b`                    |
| `RegexMatcherBuilder::whole_line` | ~270 | method | Wrap in `^ … $`                                  |
| `RegexMatcherBuilder::line_terminator` | ~280 | method | Required for line-mode optimizations              |
| `RegexMatcher`               | 366  | struct   | The built matcher                                   |
| `RegexMatcher::new`          | 385  | fn       | Convenience: builder with defaults                 |
| `RegexMatcher::new_line_matcher` | 401 | fn     | Convenience: builder with `line_terminator = \n`   |
| `RegexCaptures`             | ~519 | struct   | `Captures` impl wrapping `regex_automata` captures |
| `impl Matcher for RegexMatcher` | 409 | impl   | See trait methods overridden below                |

**Trait methods overridden (lines 412–506):**

| Method                            | Override? | Notes |
|-----------------------------------|-----------|-------|
| `find_at`                         | yes       | Uses `regex.find(Input::new(haystack).span(at..))` |
| `new_captures`                    | yes       | Wraps `regex.create_captures()` in `RegexCaptures` |
| `capture_count`                   | yes       | Delegates to `regex.captures_len()`                |
| `capture_index`                   | yes       | Delegates to `regex.group_info().to_index(...)`    |
| `try_find_iter`                   | yes       | Iterates `regex.find_iter(haystack)`                |
| `captures_at`                     | yes       | Uses `regex.search_captures(&input, caps)`          |
| `shortest_match_at`               | yes       | Uses `regex.search_half(&input)` (faster than find) |
| `non_matching_bytes`              | yes       | Returns `Some(&self.non_matching_bytes)`            |
| `line_terminator`                 | yes       | Returns `self.config.line_terminator`               |
| `find_candidate_line`             | yes       | Returns `Candidate` if `fast_line_regex` is set, else `Confirmed` via `shortest_match` |

**Side effects:** none. The struct owns immutable state after construction.

**Tests:** 6 inline `#[test]` blocks at lines 553+. See
`crates/regex/src/matcher.rs:553-670`.

---

## `crates/regex/src/config.rs`

**Purpose:** `Config` struct (10+ boolean knobs) + `ConfiguredHIR` (HIR with
applied transformations like `whole_line`, `word`, `line_terminator`).

**Public types:**

| Item              | Line | Kind   | Notes                                    |
|-------------------|------|--------|------------------------------------------|
| `Config`          | 24   | struct | `pub(crate)` — 13 knobs                  |
| `Config::default` | 45   | impl   | `multi_line=false`, `unicode=true`, …    |
| `ConfiguredHIR`   | 157  | struct | Wraps HIR + Config                       |
| `Config::build_many` | 71 | impl  | Patterns → `ConfiguredHIR`               |
| `ConfiguredHIR::into_whole_line` | ~ | method | Wrap HIR in `^…$`                |
| `ConfiguredHIR::into_word`     | ~ | method | Wrap HIR in `\b…\b`              |
| `ConfiguredHIR::to_regex`       | ~ | method | → `regex_automata::meta::Regex`  |
| `ConfiguredHIR::non_matching_bytes` | ~ | method | → `ByteSet`                   |
| `ConfiguredHIR::line_terminator` | ~ | method | from HIR analysis                |

No tests inline; the integration tests in `tests/` exercise it.

---

## `crates/regex/src/error.rs`

**Purpose:** typed error with byte-exact `Display` strings.

**Public API:**

| Item                  | Line | Kind   | Notes                                    |
|-----------------------|------|--------|------------------------------------------|
| `Error`               | 7    | struct | wraps `ErrorKind`                        |
| `Error::kind`         | 34   | fn     | `pub fn kind(&self) -> &ErrorKind`       |
| `ErrorKind`           | 42   | enum   | `#[non_exhaustive]` — variants below     |
| `ErrorKind::Regex(String)` | 48 | variant | Parsing or compile error             |
| `ErrorKind::NotAllowed(String)` | 58 | variant | Literal byte forbidden in pattern  |
| `ErrorKind::InvalidLineTerminator(u8)` | 62 | variant | Non-ASCII line term     |
| `ErrorKind::Banned(u8)` | 64 | variant | Byte is in the banned set            |
| `impl Display for Error` | 69 | impl | Each variant emits a fixed string (see below) |

**Byte-exact `Display` strings (must be preserved verbatim):**

| Variant                   | Exact output                                  |
|---------------------------|-----------------------------------------------|
| `Regex(s)`                | `{s}`                                         |
| `NotAllowed(lit)`         | `the literal {lit:?} is not allowed in a regex` |
| `InvalidLineTerminator(b)`| `line terminators must be ASCII, but {b:?} is not` |
| `Banned(b)`               | `pattern contains {b:?} but it is impossible to match` |

(`b:?` uses `bstr::ByteSlice::as_bstr` for human-readable ASCII bytes;
non-printable bytes render as escape sequences. The format is part of the
contract — callers match on substring "is not allowed" etc.)

---

## `crates/regex/src/ast.rs` (small)

**Purpose:** analyse the parsed regex AST to find inner literals, banned
bytes, and the line-terminator byte that can never appear in a match.

Public: `AstAnalysis`. Methods: `static_analysis`, `first_byte_set`,
`required_literal`, etc. ~216 LOC.

## `crates/regex/src/literal.rs` (small)

**Purpose:** extract one or more literals from a configured HIR — these
become the `fast_line_regex` candidate generator. ~670 LOC.

## `crates/regex/src/ban.rs`, `non_matching.rs`, `strip.rs`

Small helper modules. No public API beyond what `matcher.rs` uses internally.