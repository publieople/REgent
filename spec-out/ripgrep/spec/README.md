# ripgrep (regex-engine scope)

`ripgrep` is a line-oriented search tool that recursively searches the
current directory for a regex pattern while respecting gitignore rules.

This spec covers **only** the regex engine: `crates/regex/` and its sibling
`crates/matcher/` (the trait it implements). The original repository is at
<https://github.com/BurntSushi/ripgrep>. Version at time of capture:
`ripgrep 15.2.0` (commit `227381d`).

## What the regex engine does

A user-facing tool needs three things: a way to express "find me a match",
a way to walk through matches over a stream of bytes, and a way to plug in
different match algorithms (regex, literal substring, PCRE2, …) behind a
common interface.

ripgrep splits this:

- `crates/matcher` defines the `Matcher` trait — the abstract interface
  every search backend implements.
- `crates/regex` provides an implementation of `Matcher` on top of Rust's
  `regex_automata` engine. It is the *default* matcher.
- `crates/searcher` drives a `Matcher` over a haystack, callback-style.
- `crates/core` parses CLI flags and wires everything together.

This spec rebuilds the first two pieces from scratch.

## File roles

| Path | Role | Scope |
|---|---|---|
| `crates/matcher/src/lib.rs` | Trait definition `Matcher` | in scope |
| `crates/regex/src/lib.rs` | Crate entry, re-exports | in scope |
| `crates/regex/src/matcher.rs` | `RegexMatcher`, `RegexMatcherBuilder`, `impl Matcher` | in scope |
| `crates/regex/src/config.rs` | Internal `Config` knobs | in scope |
| `crates/regex/src/error.rs` | `Error`, `ErrorKind` | in scope |
| `crates/regex/src/ast.rs` | AST analysis helpers | in scope (small) |
| `crates/regex/src/literal.rs` | Inner-literal extraction | in scope (small) |
| `crates/regex/src/ban.rs` | Banned-byte check | in scope (small) |
| `crates/regex/src/non_matching.rs` | Non-matching-byte analysis | in scope (small) |
| `crates/regex/src/strip.rs` | Strip-matches-from-haystack helper | in scope (small) |
| `crates/core/main.rs` | CLI entry | out of scope |
| `crates/searcher/src/**` | Search driver | out of scope |
| `crates/ignore/src/**` | `.gitignore` walker | out of scope |
| `crates/pcre2/src/**` | Alternative PCRE2 backend | out of scope (reuses trait) |