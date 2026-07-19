---
name: regent-reverse
description: Use when the user asks to reverse-engineer a Git repository into a structured natural-language spec, write a structured spec for any codebase, or generate "repo → spec/" output. Triggers on phrases like "还原这个仓库", "把仓库转成 spec", "reverse engineer <url>", "生成结构化说明", or when the user supplies a repo URL/path and asks REgent to describe it. Drives the agent to deeply explore the entire codebase (every file, every test, every config) before writing the spec tree. Works across Python, Rust, Go, and other languages — the rules are language-aware only where they have to be (e.g. `trait` vs `Protocol` vs interface).
version: 0.3.0
author: REgent contributors
license: GPL-3.0-or-later
metadata:
  hermes:
    tags: [regent, reverse-engineering, spec, codebase-analysis]
    related_skills: [plan, requesting-code-review]
---

# regent-reverse

Reverse a Git repository into REgent's structured `spec/` tree. The output is a
catalog an AI coding agent can read end-to-end to rebuild the project from
scratch.

## When to Use

- User gives a repo URL (or local path) and asks to reverse it, describe it,
  or "make a spec".
- User asks "what does this repo do" with a need for deep, structured output
  rather than a chatty answer.
- The next step will be a build/refactor pipeline that needs a stable
  spec schema as input.

**Don't use for**: a single-line "what does this file do", quick Q&A about a
repo, or any task where a structured tree is overkill.

## Inputs

- `repo_url` or local path (REQUIRED)
- `out_dir` where `spec/` will be written (defaults to `./spec-out/<repo-name>/`)
- `depth` — `quick` | `normal` (default) | `deep`. Affects how exhaustive
  per-file analysis is. `quick` skips test-file deep dives.
- `scope` — `whole` (default) | `single-module <name>` | `single-file <path>`.
  For repos >30 modules you almost always want a focused scope; a full
  scan on a large repo can blow the budget. Pick by intent: pick the
  module that most users touch (e.g. `console.py` for `rich`).
  When you pick anything other than `whole`, note the choice at the top
  of `AGENTS.md` and write `specs/_scope.md` listing the modules you did
  NOT cover (one line each is enough).

## Workflow (the agent MUST follow in order)

Each step ends with a checkable condition. Do not advance until the previous
step's condition is true.

### 1. Acquire

- For a URL: `git clone --depth 1 <url>` into a temp worktree.
- For a local path: copy or use in place. Never mutate the source.
- Verify: `ls <worktree>` shows entry files (README, package.json / pyproject /
  Cargo.toml / go.mod / etc.).

### 2. Recon (mandatory full-tree scan)

The agent MUST inspect every entry in the tree, including hidden files
(.github/, .vscode/, CI configs, Dockerfile, license headers). For each entry
record: path, kind (code | config | doc | test | asset | build | ci), rough
LOC, language/format.

Verification: produce a file count tally — total files, code files, test
files, config files. The tally must be non-zero in every category unless the
project genuinely lacks one.

### 3. Module / dependency mapping

Before per-file reading, identify:

- Top-level directory layout (`src/`, `lib/`, `cmd/`, `internal/`, etc.).
- Public entry points (CLI entry, main, `__init__.py`, exported package).
- Module boundaries — which directories are cohesive units?
- Dependency graph: imports between modules. Use `grep` over `import` /
  `from` / `use` / `#include`.

If the repo has 30+ top-level files, do this with a quick scan, not full read.

**Lazy-import note:** many real-world modules import dependencies *inside*
function bodies (`from .jupyter import display` inside a method). A top-of-file
`grep` misses these. Re-run the import scan after step 4 reveals them; any
module that imports lazily MUST be listed in `architecture-rules.md` with the
trigger site. **Rust analog:** `use …` inside function bodies AND
`#[cfg(target_os = "…")]` platform gates — both are visibility-class
boundaries and must be re-grepped after step 4.

### 4. Per-file deep read (lazy rule: read all source and all tests)

This is the core step. **Do not skim.** For every source file and every
test file, record:

- One-line purpose (what, not how).
- Public API: function/class names + signatures + 1-line behavior.
- Notable invariants: preconditions, error paths, side effects, locks.
- Test coverage hint: which test file(s) exercise this code.

For docs and config, summarize intent only — full API capture is for code.

**Skip**: generated files (under `dist/`, `build/`, `node_modules/`, lock
files), vendored deps, large binary blobs. List them with one line.

### 5. Inferred conventions

Mine the codebase for:

- Style: indentation, quote style, line length, formatter presence (look for
  `.editorconfig`, `.prettierrc`, `pyproject.toml [tool.black]`, etc.).
- Type system usage.
- Error handling patterns.
- Test framework and patterns (fixture style, mocking, parametrization).
- Build / lint commands (from `package.json scripts`, `tox.ini`,
  `Makefile`, `.github/workflows/`).
- `# pragma: no cover` markers — they encode platform-conditional code
  (e.g. Windows-only branches). Note them in `architecture-rules.md` so
  the rebuild agent knows gaps are intentional.
- **Compile-time backend selection:** if the project has a feature-flag
  mechanism (Rust `[features]` in `Cargo.toml`, Python `extras_require`,
  Go build tags), list each feature, what it gates, and the default
  state in `conventions/dev-env.md`. Hidden compile-time paths break a
  rebuild silently.

Verification: every inferred rule is sourced — quote the file/line.

**Files that own I/O (printing, network, filesystem) MUST produce an
entry in `architecture-rules.md` covering:** exception-to-exit policy,
`SystemExit` paths, std-stream side effects (`os.dup2`, broken-pipe
handling). A rebuild that misses these will pass unit tests and fail in
production. For Rust the analog scan keywords are `std::fs`, `std::io::Write`,
`process::exit`, `#[cfg(target_os = "…")]` — same rule, different syntax.

### 6. Build the functional inventory

Enumerate user-observable behaviors and verification commands. Examples:

- "Running `<cmd> --help` prints usage and exits 0."
- "`pytest` runs N tests, all pass."
- "Tool round-trips input file X to output identical to expected Y."

This list becomes `inventory/functional-checklist.md` and is the **build
phase's grading key**. Aim for 10–50 entries depending on repo size; small
repo may have fewer.

### 7. Emit spec tree

Write to `<out_dir>`:

```
spec/
├── AGENTS.md            # Index + rebuilding instructions (one file)
├── README.md            # Human overview of the original project
├── architecture.md      # Goals / quality goals / building blocks (arc42-lite)
├── layout/
│   ├── tree.txt         # Original tree (sortable, with annotations)
│   └── src.map.md       # File → purpose + public API
├── specs/
│   └── <module>.spec.md # One per module: should/must + Scenarios
├── conventions/
│   ├── code-style.md
│   ├── dev-env.md       # Build / test / lint commands
│   └── architecture-rules.md
└── inventory/
    └── functional-checklist.md
```

File rules:

- `AGENTS.md` is **mandatory** and is the first file a coding agent reads.
  It links to the rest and tells the agent to use this spec to rebuild from
  scratch, not to copy code.
- Each `specs/*.spec.md` uses OpenSpec-lite form:
  `## Purpose` / `## Requirements` (with SHOULD/MUST) / `## Scenarios`
  (WHEN...THEN... form).
- Each spec MUST include a literal table of any human-facing output
  strings (greetings, error prefixes, log formats), byte-for-byte. The
  rebuild agent must not have to infer punctuation from a checklist.
- Each spec MUST spell out the exit-code prefix for CLI error paths if
  applicable (e.g. `error: <message>` to stderr). If the module has **no
  CLI entry**, substitute: list every exception type it raises with
  byte-exact messages for non-`DebugError` ones.
- A `if __name__ == "__main__":` block in any source file is **NEVER part
  of the contract** — record it in `layout/src.map.md` with
  `role: self-demo, not API`. A rebuild must omit it. **Language-agnostic
  rule:** any *self-test* or self-demo entry point is not contract —
  in Rust this is `#[cfg(test)] mod tests { … }` blocks or test-only
  helper `fn`s. The real `fn main()` of a binary crate IS contract.
- For every `Protocol` / `ABC` / `trait` / interface declared in the scanned
  source, list every abstract / duck-typed method in the spec's `R-`
  section, with the caller dispatch site (`hasattr(x, '__rich_console__')`
  in Python, `&dyn Trait` / `impl<T: Trait> Trait for &T` blanket impls in
  Rust). Protocol contracts are silently invisible to importers; the spec
  must carry them.
- `conventions/*.md` cites files and line numbers wherever it states a rule
  — every rule must be evidence-backed.
- `inventory/functional-checklist.md` is plain markdown checklist,
  machine-greppable. Each entry has a `- [ ]` form and a verification
  command.
- Spec does not pin `pyproject.toml` metadata fields (description,
  author), `LICENSE` body, or `README.md` content — those are
  presentation, not contract. The rebuild invents them.

### 8. Self-review

Before declaring done:

- All categories of files from step 2 accounted for in some output file.
- Every module has a spec OR a documented reason to skip.
- Every inferred convention in `conventions/` cites a source.
- The functional checklist has at least one entry per public CLI command /
  script / API surface.
- Run `tree <out_dir>` (or equivalent) and verify the layout matches step 7.

## Common Pitfalls

1. **Skimming the tree.** The whole point is *thoroughness*. If you read
   fewer than 80% of source files, redo this step.
2. **Hallucinating APIs.** Public APIs MUST come from the actual source. If
   you cannot confirm a name exists, omit it; never invent.
3. **Generic conventions.** "Use camelCase" without evidence is noise. Every
   rule needs a sample file or config that backs it (`rustfmt.toml` line 1,
   `.editorconfig`, `[tool.black]`, etc.) — language-agnostic, citation-based.
4. **Conflating original code with spec.** The spec describes what the
   project *does and why* — not line-for-line code. If `src.map.md` starts
   copying source, rewrite it.
5. **Skipping tests.** Tests reveal the project's true contract. Read them.
6. **Missing functional checklist.** Without it the build phase has no
   grading key. Don't ship without one.
7. **Treating lazy imports as trivial / missing them in the dep graph.**
   Many real-world modules defer heavy imports (`display`, `windows-only`,
   `LegacyWindowsTerm`) into method bodies. A top-of-file `import` grep
   reports zero deps. Re-scan after step 4 catches them.

## Verification Checklist

- [ ] Repo acquired without mutating the source.
- [ ] Full tree scanned; tally recorded in step 2.
- [ ] Module + dependency graph sketched.
- [ ] Every source file and every test file has at least one entry in
      `layout/src.map.md`.
- [ ] Each module has `specs/<module>.spec.md` with Purpose, Requirements,
      Scenarios.
- [ ] `conventions/*.md` cite file:line for every rule.
- [ ] `inventory/functional-checklist.md` has 10+ entries (or fewer if
      genuinely small repo, in which case state why).
- [ ] `AGENTS.md` is written and links the rest.
- [ ] `tree <out_dir>/spec` matches the layout in step 7.
- [ ] If scope ≠ whole, `specs/_scope.md` exists and lists every skipped
      module with a one-line reason.
- [ ] If any scanned file declared a `Protocol`/`ABC`/`trait`/interface,
      every abstract / required method appears as an `R-` requirement
      somewhere.
- [ ] If the project has compile-time feature flags (`[features]`,
      build tags, optional deps), every feature is documented in
      `conventions/dev-env.md` with what it gates.

## One-Shot Recipe

```bash
# From REgent project root
git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/repo
# Then run regent-reverse skill, supplying the path
# Output appears at ./spec-out/<repo>/spec/
```
