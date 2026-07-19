---
name: regent-refactor
description: Use when the user asks to refactor an existing project against a modified spec, regenerate code from a changed spec, or refactor a "shit-mountain" codebase (屎山重构) back to documented intent. Triggers on phrases like "refactor to spec", "按新 spec 改", "regenerate from <spec_dir> with new requirements", or "重写这个屎山". Pairs with regent-reverse + regent-build — reverse produces a spec, the user edits specs/ to change intent, this skill rewrites the codebase to match the edited spec. Grade key is the same as regent-build: both functional-checklist.md and inventory/test-oracle.md must stay green.
version: 0.2.0
author: REgent contributors
license: GPL-3.0-or-later
metadata:
  hermes:
    tags: [regent, refactor, subagent, reverse-roundtrip, test-oracle]
    related_skills: [regent-reverse, regent-build, plan]
---

# regent-refactor

Apply a modified REgent spec to an existing codebase (or to a fresh
checkout). The user has edited `specs/<module>.spec.md` (and/or
`inventory/functional-checklist.md`, `inventory/test-oracle.md`,
`conventions/*.md`) to change intent. This skill rewrites the source
tree so the new spec is satisfied, and proves it by running the
graded test suite (black-box checklist + white-box oracle).

Refactor ≠ rebuild. Refactor preserves intent that the user kept
(unchanged spec sections) and only mutates code where the spec
demands a new behaviour. Rebuild would throw the whole project away.
Read the diff first, mutate surgically.

## When to Use

- A spec tree exists and has been edited since the last reverse.
- The user wants the codebase aligned to the edited spec without a
  full ground-up rebuild.
- A "shit-mountain" project needs to be brought under a spec —
  reverse it (regent-reverse), then refactor it (this skill) one
  spec change at a time.

**Don't use for**:
- First-time spec generation — that is regent-reverse.
- Verifying an unmodified spec — that is regent-build.
- Editing code without a spec to point at — this skill assumes the
  intent is captured somewhere in `<spec_dir>`.

## Inputs

- `spec_dir` (REQUIRED) — path to the **edited** spec tree.
- `source_dir` (REQUIRED) — path to the existing codebase that
  reflects the **pre-edit** spec. The agent will mutate this in place
  (or write to a sibling `out_dir`, see `strategy`).
- `strategy` — `in-place` (default, mutates `source_dir` after
  snapshot) | `side-by-side` (writes to `out_dir` for diffing).
  Default is in-place because refactor scenarios usually want the
  project on disk to stay current.
- `out_dir` — only used with `strategy: side-by-side`. Default is a
  sibling of `source_dir` named `<source_dir>-refactored`.

## Workflow (MUST follow in order)

### 1. Diff the spec

Before touching code, identify what changed. The user's edit is
authoritative for intent.

- For each tracked file under `<spec_dir>` (especially
  `specs/*.spec.md`, `inventory/functional-checklist.md`,
  `inventory/test-oracle.md`, `conventions/*.md`):
  - If the file has a `## Edited:` or `## Changelog:` heading
    written by the user, use it.
  - Else, do a content diff vs the project history if a `.git` is
    available under `<spec_dir>` (REgent specs may be versioned).
  - Else, ask the user what changed. Do **not** guess.
- Record the diff in a working note (in-memory; do not commit a
  scratch file unless the user asks).
- **Pure-clarification edits are legitimate.** If the diff only
  adds precision to an existing requirement without changing
  inputs, outputs, error paths, or exit codes, classify as
  `Pure clarification` per §2 and skip code edits entirely. The
  downstream symbol list (§2) can be empty; that is a passing
  outcome, not a skipped one.

### 2. Classify the change

For each `R-` / `S-` / oracle entry the user added, removed, or
edited:

- **Behaviour change** (R-/S- edit that alters inputs, outputs, or
  error paths) → rewrite affected module(s). Example: `greet`
  now raises on `name == "Bot"` in addition to empty.
- **Conventions change** (edit in `conventions/*.md`) → adjust
  style, imports, error types. Example: use `httpx` not `requests`.
- **Inventory change** (checklist or oracle count shift) → may need
  new behaviour, but the spec module sections are the source of
  truth for what that behaviour is. If a new oracle entry has no
  matching `R-`, the spec is incomplete — flag it back to the user
  before rewriting code.
- **Pure clarification** (more precise wording, no semantic shift)
  → no code change needed.

For each affected module, list the **specific** symbols that must
change, with file:line targets.

### 3. Snapshot before mutating

If `strategy: in-place`:

- Run `git status` in `source_dir`. If dirty, stop and ask the user
  to commit or stash.
- If clean, snapshot via `git worktree add ../<source_dir>-snapshot
  <HEAD>~0` OR a tarball. The snapshot is the rollback point if
  this skill corrupts the tree. **Mandatory: snapshot MUST succeed
  before the rewriter is spawned.**

If `strategy: side-by-side`: copy `source_dir` to `out_dir`. The
original `source_dir` itself is the rollback; no separate snapshot
needed.

### 4. Spawn the rewriter subagent

Use `delegate_task` with these properties:

- `role: leaf`
- Goal must contain: `spec_dir`, the source dir (or `out_dir`), the
  diff of the spec, the list of symbols that must change from step
  2, the test command from `<spec_dir>/conventions/dev-env.md`.
- The rewriter's job is to edit **only** the symbols listed in
  step 2. It is forbidden to refactor unrelated code, even if the
  code looks ugly — that is style, not behaviour, and would defeat
  the round-trip audit.
- The rewriter must NOT regenerate code from scratch (unlike
  regent-build). It must `read_file` → `patch` → re-run pytest.
- The rewriter's final report must include a diff (before vs after
  for each changed symbol) so the user can spot accidental
  over-rewriting.

### 5. Run verification — both grading keys

After the rewriter reports:

- Run the test command from `conventions/dev-env.md`. Capture exit
  code. (This is the suite the project already has — same as a
  manual developer would run.)
- Execute every line of `functional-checklist.md` against the
  result (re-run each command / import / CLI).
- Execute every `### <symbol>` block in `test-oracle.md` against
  the result (call the function with the documented input, check
  the documented output).
- ALL THREE must be green: pytest, checklist, oracle.
- **Clarification-derived oracle:** if the spec edit added a new
  `R-`/`S-` clause, the rewriter MUST also add an `### <symbol>`
  block to `test-oracle.md` (or a scratch verification command) that
  exercises the clarification explicitly, even when no code change
  was needed. Without this, the clarification is a documented intent
  that no test actually pins.

### 6. Decide

- **All three green AND `git diff --stat source_dir out_dir` is empty:**
  this is the **clarification-only** outcome. Report
  *"Clarification-only refactor: zero source changes, spec edit is
  documented intent only."* Treat this as a successful outcome, not
  a failure to edit. Show the new oracle entry as the proof that
  the clarification is exercised.
- **All three green AND the diff is non-empty:** state the changed
  symbols (file:line diff summary) and confirm the spec edit is
  now in the code.
- **Anything red** → do not auto-rollback. Report which item, the
  actual vs expected, and the offending code path. The user
  decides whether to: (a) tweak the rewriter's diff, (b) amend the
  spec to match the code reality, or (c) roll back the snapshot.
- **Rewriter touched code outside its scope** → flag the diff.
  This is a regression of trust — the rewriter overstepped its
  brief. Roll back those edits, retry with a sharper scope.

### 7. Self-review

Before declaring done:

- [ ] Step 1 diff is recorded (in memory or scratch file).
- [ ] Step 2 symbol-level change list is recorded.
- [ ] Source tree is in a git checkpoint if in-place was used.
- [ ] All three grading keys (pytest + checklist + oracle) green.
- [ ] Rewriter's diff matches the symbol list. Nothing else.
- [ ] User informed of changed symbols with file:line.

## Common Pitfalls

1. **Reflavoring everything.** The rewriter's mandate is the diff
   in step 1. Modules untouched by the diff MUST remain
   byte-identical (modulo whitespace) — otherwise the audit breaks.
   Grep the diff before sign-off.
2. **Reading the original repo for inspiration.** Refactor is
   allowed to read `source_dir` (it is the codebase being edited).
   It is NOT allowed to look up training-data versions of similar
   projects to fill in — that smuggles in intent not in the spec.
3. **Trusting the rewriter's "I changed it" report without
   diffing.** Always run `git diff --stat` against the snapshot.
   The agent can claim it changed 5 lines and actually rewrite
   500.
4. **Adding tests not in the spec.** The oracle is the only
   white-box grading key. New behaviour the user did not write an
   oracle entry for is not graded — adding a "while I'm here" test
   is a different skill.
5. **Skipping the snapshot.** A bad refactor on a dirty tree
   corrupts the user's history. Snapshot or refuse.

## Verification Checklist

- [ ] Spec diff is identified by the user, not inferred.
- [ ] Source tree is snapshotted (in-place) or copied (side-by-side).
- [ ] Symbol-level change list matches the spec diff exactly.
- [ ] The rewriter did not touch code outside that list.
- [ ] `pytest` exit code green.
- [ ] Every `- [ ]` line of `functional-checklist.md` verified.
- [ ] Every `### <symbol>` of `test-oracle.md` executed.
- [ ] User received the file:line diff summary.

## One-Shot Recipe

```bash
# After regent-reverse produced a spec, the user has edited it.
# Now invoke regent-refactor with:
#   spec_dir   = ./spec-out/<repo>/spec
#   source_dir = /path/to/the/checked-out-repo
#   strategy   = in-place
# Expect a pass/fail report AND a diff summary that the user can
# eyeball against their spec edit.
```
