# specs/regex.spec.md — `crates/regex` (and `crates/matcher`)

OpenSpec-lite: Purpose / Requirements / Scenarios.

## Purpose

Provide an implementation of `grep_matcher::Matcher` that compiles a regex
pattern via `regex_automata::meta::Regex`, exposes all the standard regex
flag set as a builder API, and supports capture groups. The matcher is
the **default** search backend for ripgrep.

## Requirements

### REQ — the trait contract (must inherit from `grep_matcher`)

- **R1** — A `RegexMatcherBuilder` exists with a constructor
  `RegexMatcherBuilder::new() -> Self` and a method
  `build(&self, pattern: &str) -> Result<RegexMatcher, Error>`.
- **R2** — A `RegexMatcherBuilder::build_many<P: AsRef<str>>(&self, &[P]) -> Result<RegexMatcher, Error>` exists and accepts 1..N patterns joined as alternation.
- **R3** — A `RegexMatcherBuilder::build_literals<B: AsRef<str>>(&self, &[B]) -> Result<RegexMatcher, Error>` exists and is equivalent to `build_many` for literal-only inputs.
- **R4** — `RegexMatcher` implements `grep_matcher::Matcher` with
  - `type Captures = RegexCaptures`
  - `type Error = grep_matcher::NoError`
- **R5** — `RegexMatcher::find_at(&self, haystack: &[u8], at: usize) -> Result<Option<Match>, NoError>` MUST return the first match starting at byte `at` or after; if no match exists, MUST return `Ok(None)`.
- **R6** — `RegexMatcher::shortest_match_at` MUST be implementable to return the end-offset of the first match using a faster path than `find_at` (uses `regex.search_half`).
- **R7** — `RegexMatcher::non_matching_bytes` MUST return `Some(&ByteSet)` if the analysis succeeded, `None` otherwise.
- **R8** — `RegexMatcher::line_terminator` MUST return `Some(LineTerminator)` if a line terminator was configured.
- **R9** — `RegexMatcher::find_candidate_line` MUST return `Candidate(offset)` when an inner-literal fast regex found a candidate; MUST fall back to `Confirmed(offset)` via `shortest_match` when no fast regex is available.

### REQ — builder flags

- **R10** — The following flags MUST exist on `RegexMatcherBuilder` and
  default to `false` unless stated otherwise:
  - `case_insensitive(bool)`
  - `case_smart(bool)`
  - `multi_line(bool)`
  - `dot_matches_new_line(bool)`
  - `swap_greed(bool)`
  - `ignore_whitespace(bool)`
  - `unicode(bool)` — default `true`
  - `octal(bool)`
- **R11** — Numeric limit setters (return `&mut Self`):
  - `size_limit(usize)`
  - `dfa_size_limit(usize)`
  - `nest_limit(usize)`
- **R12** — Boolean group setters:
  - `word(bool)` — wraps the pattern in `\b … \b` after `into_word()`
  - `whole_line(bool)` — wraps the pattern in `^ … $` after `into_whole_line()`
  - `line_terminator(Option<LineTerminator>)` — passes through to `Config`

### REQ — smart-case semantics

- **R13** — When `case_smart(true)` is set, the matcher MUST enable
  case-insensitive matching **iff** the pattern contains at least one
  literal character AND none of its literal characters are uppercase
  per Unicode.
- **R14** — `case_smart(true)` MUST override any prior `case_insensitive(true)`
  call (smart-case is the higher-precedence knob).

### REQ — convenience constructors

- **R15** — `RegexMatcher::new(pattern: &str) -> Result<RegexMatcher, Error>`
  is shorthand for `RegexMatcherBuilder::new().build(pattern)`.
- **R16** — `RegexMatcher::new_line_matcher(pattern: &str) -> Result<RegexMatcher, Error>` sets `line_terminator = Some(b'\n')` and returns `Err(ErrorKind::NotAllowed)` if the pattern contains a literal `\n`.

### REQ — error contract

- **R17** — `Error` has variants (from `error.rs:42-65`):
  `Regex(String)`, `NotAllowed(String)`, `InvalidLineTerminator(u8)`,
  `Banned(u8)`. The enum is `#[non_exhaustive]`.
- **R18** — `Display` for `Error` MUST emit exactly:
  - `Regex(s)` → `"{s}"`
  - `NotAllowed(lit)` → `"the literal {lit:?} is not allowed in a regex"`
  - `InvalidLineTerminator(byte)` → `"line terminators must be ASCII, but {byte:?} is not"`
  - `Banned(byte)` → `"pattern contains {byte:?} but it is impossible to match"`
- **R19** — `Error` implements `std::error::Error` (marker — no source() override).

### REQ — captures contract (mirrors Python Protocol method list)

> **This is the `R-` block demanded by the skill's Protocol/ABC rule.**
> `RegexCaptures` is the concrete `Captures` type. Its trait method
> contract is `Captures` from `grep_matcher`:

- **R20** — `impl Captures for RegexCaptures`:
  - `len(&self) -> usize` — number of capture groups
  - `get(&self, i: usize) -> Option<Match>` — capture group `i`; index `0` is the overall match
- **R21** — `RegexCaptures::new(captures: regex_automata::util::captures::Captures) -> Self`
  is the only public constructor.

### REQ — blanket trait

- **R22** — `grep_matcher::Matcher` has a blanket `impl<'a, M: Matcher> Matcher for &'a M`
  (covers every method by delegating to `(*self).method(...)`). A rebuild
  of `Matcher` MUST include this blanket. (Line ~766 of `crates/matcher/src/lib.rs`.)

## Scenarios

- **S1** — WHEN calling `RegexMatcher::new("foo")?.find(b"the foo bar")?`,
  THEN the result is `Ok(Some(Match::new(4, 7)))`.
- **S2** — WHEN calling `RegexMatcher::new("foo")?.is_match(b"bar")?`,
  THEN the result is `Ok(false)`.
- **S3** — WHEN calling `RegexMatcherBuilder::new().case_insensitive(true).build("Foo")?.is_match(b"FOO")?`,
  THEN the result is `Ok(true)`.
- **S4** — WHEN calling `RegexMatcherBuilder::new().case_smart(true).build("abc")?.is_match(b"ABC")?`,
  THEN the result is `Ok(true)` (smart case activates for all-lowercase).
- **S5** — WHEN calling `RegexMatcherBuilder::new().case_smart(true).build("Abc")?.is_match(b"ABC")?`,
  THEN the result is `Ok(false)` (smart case does NOT activate for mixed-case).
- **S6** — WHEN building a matcher with `RegexMatcherBuilder::new().multi_line(true).build("^foo")?`,
  THEN `is_match(b"bar\nfoo")?` returns `Ok(true)`.
- **S7** — WHEN calling `RegexMatcherBuilder::new().build("\\invalid")?`,
  THEN the result is `Err(Error)` with `kind() == ErrorKind::Regex(...)`.
- **S8** — WHEN calling `RegexMatcher::new_line_matcher("foo\nbar")?`,
  THEN the result is `Err(Error)` with `kind() == ErrorKind::NotAllowed("\n".to_string())`.
- **S9** — WHEN building a matcher with a `line_terminator` and a regex with a discoverable inner literal, THEN `find_candidate_line` returns `LineMatchKind::Candidate(offset)` for lines containing the literal.
- **S10** — WHEN `find_iter` is called on `haystack` containing zero-width matches (e.g. pattern `a*`), THEN iteration MUST make progress (not loop forever) and MUST NOT return two empty matches at the same position.
- **S11** — WHEN `RegexMatcherBuilder::new().size_limit(0).build("(a+)+b")?` is called on a pathological pattern, THEN the result is `Err(Error)` of kind `ErrorKind::Regex(...)` whose Display starts with `"compiled regex exceeds size limit of "`.

## Protocol contract (skill v0.2.0 mirror)

The `Matcher` trait in `grep_matcher` is the abstract contract.
Every required method MUST be implemented on `RegexMatcher`:

| Required method           | Implemented in `matcher.rs` at | Behavior one-liner |
|---------------------------|-------------------------------|---------------------|
| `find_at`                 | line 414                      | First match after `at` |
| `new_captures`            | line 424                      | Empty `RegexCaptures` |
| `type Captures`           | line 410                      | `RegexCaptures` |
| `type Error`              | line 411                      | `NoError` |
| (overridden) `shortest_match_at` | line 471                 | Uses `search_half` |
| (overridden) `find_candidate_line` | line 491                | `Candidate` or `Confirmed` |
| (overridden) `non_matching_bytes` | line 481                | `Some(&ByteSet)` |
| (overridden) `line_terminator` | line 486                  | `self.config.line_terminator` |
| (overridden) `try_find_iter` | line 439                   | Iterates `regex.find_iter` |
| (overridden) `captures_at` | line 458                      | Uses `regex.search_captures` |
| (overridden) `capture_count` | line 429                   | `regex.captures_len()` |
| (overridden) `capture_index` | line 434                   | `regex.group_info().to_index` |

Callers dispatch by `&M` blanket (R22), so a method can take `&dyn Matcher`
and call `m.find_at(...)` without knowing the concrete type.