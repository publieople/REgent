# conventions/dev-env.md

## Toolchain

- **Rust edition 2024** — `rust-toolchain.toml` not present, so default
  Cargo decides; `Cargo.toml` declares `rust-version = "1.96"`.
- The crate uses `regex-automata 0.4.x` and `regex-syntax 0.8.x` from
  upstream crates.io.

## Build commands

| Command | Effect |
|---|---|
| `cargo build` | Build all 9 workspace crates + the `rg` binary. |
| `cargo build --release` | Optimized build (uses `[profile.release-lto]` defaults). |
| `cargo build --release --profile deb` | Uses `[profile.deb]` for Debian package builds. |
| `cargo build --features pcre2` | Enables the PCRE2 backend via `grep/pcre2`. |
| `cargo build --no-default-features` | (No-op — there are no default features besides `pcre2`.) |

## Test commands

| Command | Effect |
|---|---|
| `cargo test --workspace` | Run all 500+ inline tests. |
| `cargo test -p grep-regex` | Run only the regex engine's tests. |
| `cargo test --test integration` | Run integration tests in `tests/tests.rs`. |
| `cargo test --doc` | Run doctests (none in regex engine, but `grep_matcher` has some). |

## Lint / format commands

| Command | Effect |
|---|---|
| `cargo fmt --all` | Apply rustfmt with `rustfmt.toml` settings. |
| `cargo fmt --all -- --check` | Verify formatting in CI. |
| `cargo clippy --all-targets` | Run default clippy lints. |

## Fuzz (optional)

- `cargo +nightly fuzz run fuzz_glob` — only targets `crates/fuzz/fuzz_targets/fuzz_glob.rs`.
- The regex engine has **no** fuzz harness in this repo (intentional
  upstream, since `regex-automata` has its own).

## Platform conditionality

| Target | Effect | File:line |
|---|---|---|
| `cfg(all(target_env = "musl", target_pointer_width = "64"))` | Use jemalloc as `#[global_allocator]` | `crates/core/main.rs:60` |
| Same cfg | Add `tikv-jemallocator` to deps | `Cargo.toml:67-69` |
| `cfg(test)` | Inline tests in `crates/regex/src/*.rs` | lines listed in `architecture-rules.md` |
| `cfg(unix)` / `cfg(windows)` | Not present in `crates/regex`; appears only in `crates/searcher/src/searcher/mmap.rs` and `crates/ignore/src/dir.rs` |

## Cargo features (workspace)

- `pcre2 = ["grep/pcre2"]` — opt-in PCRE2 backend. Default OFF.
  - Source: `Cargo.toml:69-71`.
- The regex engine (`crates/regex`) has **no** `Cargo.toml [features]`
  section. All functionality is unconditional.