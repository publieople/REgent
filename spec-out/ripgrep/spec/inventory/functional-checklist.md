# inventory/functional-checklist.md

Verification key for the rebuild. Each entry is `- [ ]` and machine-greppable.

## Builder API (R1-R3, R10-R12)

- [ ] `RegexMatcherBuilder::new()` returns a builder with default config.
- [ ] `RegexMatcherBuilder::default()` is identical to `::new()`.
- [ ] `RegexMatcherBuilder::build("foo")?` succeeds and produces a `RegexMatcher`.
- [ ] `RegexMatcherBuilder::build_many(&["a", "b", "c"])?` succeeds; `is_match("b")?` returns `Ok(true)`.
- [ ] `RegexMatcherBuilder::case_insensitive(true).build("Foo")?.is_match("FOO")?` → `Ok(true)`.
- [ ] `RegexMatcherBuilder::case_smart(true).build("abc")?.is_match("ABC")?` → `Ok(true)` (S4).
- [ ] `RegexMatcherBuilder::case_smart(true).build("Abc")?.is_match("ABC")?` → `Ok(false)` (S5).
- [ ] `RegexMatcherBuilder::multi_line(true).build("^foo")?.is_match("bar\nfoo")?` → `Ok(true)` (S6).
- [ ] `RegexMatcherBuilder::dot_matches_new_line(true).build("a.b")?.is_match("a\nb")?` → `Ok(true)`.
- [ ] `RegexMatcherBuilder::swap_greed(true).build("a*")?.find("aaa")?` returns the shortest match.
- [ ] `RegexMatcherBuilder::ignore_whitespace(true).build("a b")?.is_match("ab")?` → `Ok(true)`.
- [ ] `RegexMatcherBuilder::unicode(false).build(r"\w")?.is_match("é")?` → `Ok(false)`.
- [ ] `RegexMatcherBuilder::size_limit(0).build("(a+)+b")?` → `Err(Error)` of kind `Regex(...)` whose Display starts with `"compiled regex exceeds size limit of "` (S11).

## Trait contract (R4-R9, R22)

- [ ] `RegexMatcher` implements `grep_matcher::Matcher`.
- [ ] `RegexMatcher` `type Captures = RegexCaptures`.
- [ ] `RegexMatcher` `type Error = NoError`.
- [ ] `find_at(b"foo", 0)?` returns `Ok(Some(Match::new(0, 3)))` (S1).
- [ ] `find(b"foo")?` returns `Ok(None)` when no match (S2).
- [ ] `shortest_match_at(b"foo", 0)?` returns `Ok(Some(3))`.
- [ ] `non_matching_bytes()` returns `Some(&ByteSet)` after `build`.
- [ ] `line_terminator()` returns `Some(LineTerminator::byte(b'\n'))` when configured.
- [ ] `find_candidate_line(b"prefix FOO suffix")?` returns `Some(Candidate(_))` for a fast-literal pattern (S9).
- [ ] `&dyn Matcher` works (via blanket `impl<M> Matcher for &M`, R22).
- [ ] `find_iter` on `a*` over `aaa` makes progress; does not return two empty matches at same position (S10).

## Captures (R20-R21)

- [ ] `let mut caps = matcher.new_captures()?; matcher.captures(b"foo", &mut caps)?; caps.len() == 1; caps.get(0) == Some(Match::new(0, 3))`.
- [ ] `caps.get(1)` returns `None` for a no-group pattern.

## Error contract (R17-R19)

- [ ] `Display` for `ErrorKind::Regex("bad pattern".into())` is `"bad pattern"` (exact).
- [ ] `Display` for `ErrorKind::NotAllowed("\n".into())` is `"the literal '\n' is not allowed in a regex"` (exact).
- [ ] `Display` for `ErrorKind::InvalidLineTerminator(0xFF)` is `"line terminators must be ASCII, but 255 is not"`.
- [ ] `Display` for `ErrorKind::Banned(0x00)` is `"pattern contains 0 is not allowed"` — verify against actual `bstr::ByteSlice` formatting for `0x00`.
- [ ] `Error` implements `std::error::Error` (source returns `None`).

## Convenience constructors (R15-R16)

- [ ] `RegexMatcher::new("foo")?` is equivalent to `RegexMatcherBuilder::new().build("foo")?`.
- [ ] `RegexMatcher::new_line_matcher("foo\nbar")?` → `Err(ErrorKind::NotAllowed("\n"))` (S8).
- [ ] `RegexMatcher::new_line_matcher("foo")?` succeeds and `line_terminator()` is `Some(LineTerminator::byte(b'\n'))`.

## `crates/matcher` invariants

- [ ] `grep_matcher::Matcher` trait exists with `find_at` and `new_captures` required.
- [ ] `grep_matcher::Captures` trait exists with `len` and `get` required.
- [ ] `Match::new(start, end)` panics if `start > end`.
- [ ] `LineTerminator::default()` is `LineTerminator::byte(b'\n')`.
- [ ] `impl<M: Matcher> Matcher for &M` blanket impl exists (R22).

## Verification commands (machine-greppable)

```bash
# Build everything
cargo build --workspace

# Run regex engine tests only
cargo test -p grep-regex

# Run all unit tests
cargo test --workspace --lib

# Format check
cargo fmt --all -- --check

# Lint check
cargo clippy -p grep-regex --all-targets -- -D warnings

# Static analysis: confirm no I/O in crates/regex
! grep -rn 'std::fs\|std::io::Write\|std::process::exit\|println!' crates/regex/src/

# Static analysis: confirm no platform cfg in crates/regex
! grep -rn 'cfg(unix)\|cfg(windows)\|cfg(target_os' crates/regex/src/

# Static analysis: confirm trait contract present
grep -q 'fn find_at' crates/matcher/src/lib.rs
grep -q 'fn new_captures' crates/matcher/src/lib.rs
```