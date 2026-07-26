# specs/_scope.md — modules NOT covered by this spec

This spec was generated with `scope = single-module (crates/regex)`. The
following modules were inspected at the file level (size + role + tests
referenced) but their internals were NOT deep-read. Rebuilding them is out
of scope.

| Path | LOC | Why skipped |
|---|---|---|
| `crates/core/main.rs` | 483 | CLI entry; rebuild only needs `arg → flag → matcher` plumbing, not the full CLI dispatcher. |
| `crates/core/flags/**` | ~3000 | Flag parsing; the spec mentions `HiArgs` / `lowargs` only by name. |
| `crates/core/search.rs` | ~? | Search wiring; depends on the engine we're rebuilding here. |
| `crates/core/haystack.rs`, `messages.rs`, `logger.rs` | ~200 | Output formatting helpers. |
| `crates/cli/src/**` | ~8 files | CLI utilities (decompress, escape, hostname, human, pattern, process, wtr, lib). |
| `crates/globset/src/**` | ~5 files + bench | Glob matching for `--glob`. Pure utility, can be re-implemented against a stdlib globber. |
| `crates/grep/src/lib.rs` + `examples/` | ~100 | Facade crate that re-exports `matcher`, `regex`, `pcre2`, `searcher`. No logic of its own. |
| `crates/ignore/src/**` | ~9 files + tests + example | `.gitignore` walker. |
| `crates/pcre2/src/**` | ~3 files | Alternative `Matcher` impl on PCRE2; uses the same `grep_matcher::Matcher` trait. |
| `crates/printer/src/**` | ~9 files | Output formatting (color, JSON, stats, hyperlinks, summary, standard, path). |
| `crates/searcher/src/**` | ~6 files + example | The search driver; iterates a `Matcher` over a haystack. |
| `tests/*.rs` (10 files) | ~thousands | Integration tests against the `rg` binary; most need the binary rebuilt. |
| `fuzz/fuzz_targets/fuzz_glob.rs` | small | cargo-fuzz harness for glob matching. |
| `build.rs` | small | Pre-build codegen for shell completions / man pages. |
| `.github/workflows/*.yml` | small | CI/release pipelines; not code. |
| `pkg/**`, `benchsuite/**`, `scripts/**` | varies | Packaging & benchmarking artifacts. |