---
name: regent-build
description: Use when the user asks to rebuild a project from a REgent spec tree, run "spec → code + tests" roundtrip, or verify that a reverse-engineered spec is sufficient to reconstruct the original. Triggers on phrases like "按 spec 重建", "build from spec", "reconstruct from <spec_dir>", "verify spec sufficiency", or just "build". Pairs with `regent-reverse` — reverse produces the spec, this skill consumes it and produces runnable code that grades against the spec's `functional-checklist.md`. Works across languages via hermes subagent delegation.
version: 0.1.0
author: REgent contributors
license: GPL-3.0-or-later
metadata:
  hermes:
    tags: [regent, build, subagent, reverse-roundtrip]
    related_skills: [regent-reverse, plan, executing-plans]
---

# regent-build

Consume a REgent spec tree and produce runnable code that satisfies the spec's
`R-`/`S-` requirements and every line of `functional-checklist.md`. This is
the second half of the roundtrip pipeline (the first half is `regent-reverse`).

## When to Use

- A `spec/` tree exists (typically produced by `regent-reverse`) and the
  user wants to verify it is **sufficient** — i.e. an independent agent
  reading only the spec can rebuild the project.
- The user invokes `build`, `reconstruct from spec`, `verify spec`,
  `regent build <spec-dir>`, or similar.
- Bulk scenario: stress-test a spec without paying for a human rebuild.

**Don't use for**:
- Building from a fresh description (no spec yet) — use `regent-reverse`
  first to produce one.
- Modifying an existing project without a spec — that is refactor, not
  rebuild; do it manually or write a new skill for it later.
- Production deploys — the rebuild artifact is a research/verification
  output, not a release artifact.

## Inputs

- `spec_dir` — path to the spec tree (REQUIRED). Must contain
  `AGENTS.md`, `inventory/functional-checklist.md`, and `conventions/`.
- `out_dir` — where to put the rebuild. Default:
  `/tmp/rebuild-<repo-name>/`, taken from the spec's
  `README.md` first heading.
- `strategy` — `single-subagent` (default) | `multi-subagent`.
  Default is one subagent with the whole spec; multi-subagent only if
  the spec has 5+ `R-` heavy `specs/*.spec.md` files.

## Workflow (MUST follow in order)

Each step ends with a checkable condition. Do not advance until satisfied.

### 1. Verify the spec is buildable

Before spawning anything, check the spec itself is ready:

- `AGENTS.md` exists and is non-empty.
- `inventory/functional-checklist.md` exists and has at least 5
  `- [ ]` entries (fewer → spec too thin for a meaningful build;
  recommend running `regent-refine` first instead).
- If `specs/_scope.md` exists, read it. Default strategy is
  scoped (not whole-repo).
- Target language/build-tool: read it from `conventions/dev-env.md`.

If any check fails, **stop**. Report the missing piece, do not
build.

### 2. Confirm the rebuilder cannot see the original source

This is the roundtrip property we are testing. The rebuilder MUST NOT
have access to the original repo tree (no path given, no clone hint).
Whitelist only the spec directory.

Explicit guard: when delegating, set the subagent's task to start with
"You may ONLY read files under `<spec_dir>`. Do NOT touch any path
outside it. The original repo exists at `<original_path_hint>` but is
not for reading."

(If a previous step accidentally left a copy of the repo under
`out_dir`, delete it before spawning.)

### 3. Spawn the rebuilder subagent

Use `delegate_task` with these properties:

- `role: leaf` (the rebuilder cannot delegate further; keeps the
  roundtrip tight).
- The subagent's goal MUST contain: the spec path, the out path,
  the language hint, the constraint to read-only the spec.
- Tell the subagent: read `AGENTS.md` first, then follow its
  rebuild order.
- Tell the subagent: do not invent CLI features, error messages,
  formats, or behavior NOT explicitly given in the spec.
  When in doubt, prefer omission over invention.
- Tell the subagent: when done, report in the response a bullet
  list of spec sections it had to invent beyond (so the spec author
  can patch).

### 4. Run the verification

After the subagent reports done:

- `cd <out_dir>`
- Read `conventions/dev-env.md` for the exact test/build commands.
- Run the test command. Capture exit code.
- Cross-check `functional-checklist.md` line by line against the
  rebuild artifact (run each command / import each module as the
  checklist prescribes).
- Tick or fail each item; record evidence (output, exit code, log
  line).

### 5. Decide

- **All green:** the spec is sufficient. Report.
- **Any red:** the spec has a hole. Report each failing item with
  the exact failure message. **Do not edit the rebuild to make it
  pass.** That would hide the spec gap. Recommend the spec author
  add the missing piece in `R-` and re-run this skill.
- **Re-builder invented something not in spec:** that is a separate
  signal — list it. It is not a fail (the build may still pass),
  but it is a spec-debt item to fix in the next reverse iteration.

### 6. Self-review

Before declaring done, verify:

- The rebuilder subagent received NO path to the original repo.
- The rebuild artifact was NOT mutated to mask failures.
- Every checklist item has a tick or a fail reason (no skipped).
- The spec-debt list is non-empty whenever the rebuilder reported
  invention.

## Common Pitfalls

1. **Letting the rebuilder peek at the original source.** Defeats the
   whole roundtrip. The whitelist is the contract.
2. **Patching the rebuild until tests pass.** You are testing the
   spec, not the rebuild. A green rebuild with a tweaked file is a
   false green; the spec still has the gap.
3. **Skipping `conventions/dev-env.md`.** The rebuild needs the
   project's build/test commands, not the agent's defaults. uv vs
   pip vs poetry, cargo vs rustup, go vs cgo — these matter.
4. **Treating the rebuild artifact as production code.** It is a
   research output. Burn it after the report if you want.
5. **Re-using the previous rebuild directory without cleaning.**
   Stale `.venv`, stale `Cargo.lock` target/ etc. produce false
   passes. Always start from an empty (or freshly `rm -rf`'d)
   out_dir.
6. **Running a multi-pass refine loop on spec-debt inside this
   skill.** That is a different skill. regent-build runs once,
   reports, exits.

## Verification Checklist

- [ ] `AGENTS.md` and `inventory/functional-checklist.md` both exist
      and are non-empty.
- [ ] Out directory was empty (or freshly cleaned) before the
      rebuilder started.
- [ ] The subagent received only the spec path; the original repo
      path was given as a "do not read" hint at most.
- [ ] Verification commands ran from `conventions/dev-env.md` (not
      agent defaults).
- [ ] Every `- [ ]` line in `functional-checklist.md` has tick or
      fail reason; nothing skipped silently.
- [ ] Spec-debt list was produced even when the build passed.
- [ ] The rebuild artifact was NOT edited to mask failures.

## One-Shot Recipe

```bash
# After regent-reverse has produced spec at ./spec-out/<repo>/spec/
rm -rf /tmp/rebuild-<repo>
# Then invoke regent-build with:
#   spec_dir = ./spec-out/<repo>/spec
#   out_dir  = /tmp/rebuild-<repo>
#   strategy = single-subagent
# Expect a pass/fail report, a tick-by-tick checklist, and a
# spec-debt list.
```
