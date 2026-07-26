# architecture.md — arc42-lite

## 1. Goals

- Provide a line-oriented regex search backend that matches the contract
  of `grep_matcher::Matcher`.
- Translate the user-facing flag set (`-i`, `-s`, `-m`, `-x`, `-w`, …) into
  `regex_automata` configuration knobs (`case_insensitive`, `multi_line`,
  `dot_matches_new_line`, `swap_greed`, …).
- Build a `regex_automata::meta::Regex` from the configured HIR, plus an
  optional *fast-line-regex* used as a candidate generator for line-mode
  searches.
- Surface compile errors as a typed `Error` whose variants carry
  byte-exact messages a caller can match on.

## 2. Quality goals

- Zero allocation in the hot path of `find_at` (verified by `#[inline]`
  on every `Matcher` method; see `crates/regex/src/matcher.rs:412-506`).
- Backwards compatibility with the `grep-regex 0.1.x` crate API
  (this is why `crate::error::Error` exists and is re-exported).
- No panics on user input except for the documented panic in
  `grep_matcher::NoError::fmt` (which can never fire in practice).

## 3. Building blocks

```
+------------------+        +-------------------------+
| grep_matcher     |        | regex_automata          |
|   ::Matcher      |        |   ::meta::Regex         |
|   ::Match        |        |   ::Input               |
|   ::Captures     |        | regex_syntax::hir       |
|   ::LineTerm…    |        +-------------------------+
+--------┬---------+                 ^
         | implemented by            | used by
         v                           |
+--------+---------------------------+--------+
| crates/regex::matcher::RegexMatcher          |
|   config: Config                             |
|   regex: Regex                               |
|   fast_line_regex: Option<Regex>             |
|   non_matching_bytes: ByteSet                |
+-----+------------------+---------------------+
      ^ built by          ^
      |                   |
+------+----------+ +-----+-----------+
| RegexMatcherBuilder | | Config::build_many |
+--------+-----------+ +--------+---------+
         |                        |
         v                        v
    user code              HIR transformations
                           (whole_line, word, line_terminator)
```

## 4. Runtime topology

There is no runtime "main" inside `crates/regex`. The crate is a library.
The flow when a user calls `RegexMatcherBuilder::new().build("foo")`:

1. `RegexMatcherBuilder::build_many` → `Config::build_many` produces a
   `ConfiguredHIR` (HIR + applied transformations).
2. If `whole_line` is set, wrap the HIR in `^ … $` anchors.
3. Else if `word` is set, wrap in `\b … \b` anchors.
4. Convert the configured HIR to a `regex_automata::meta::Regex`.
5. Attempt to extract inner literals via `InnerLiterals::new(&chir, &regex)`
   to build the optional `fast_line_regex`.
6. Compute the `non_matching_bytes` set from the HIR.
7. Return a fully-built `RegexMatcher`.

At search time, `find_at` is the only method that does real work; everything
else in the trait dispatches to it (or to `regex_automata` for capture
support).

## 5. Cross-cutting concepts

- **Errors as enums, not strings.** Every error variant carries a typed
  payload (`String`, `u8`). The `Display` impl is byte-exact and stable.
- **Internal iteration.** The trait pushes matches to a caller-supplied
  `FnMut(Match) -> bool`. This is a deliberate design choice explained in
  `crates/matcher/src/lib.rs:14-31` and chosen over external iteration
  because some matchers can't be pulled (notably Aho-Corasick).
- **No `unsafe`.** Grepping the regex crate for `unsafe` returns nothing.