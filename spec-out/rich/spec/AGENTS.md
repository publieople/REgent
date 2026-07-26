# AGENTS — Rebuilding Rich's Console

## What this is

This spec describes **only** `rich/console.py` from
`github.com/Textualize/rich` (depth = Option B: single-module deep reverse).
It is **not** a full-spec of Rich. Other `rich.*` modules (`segment.py`,
`text.py`, `style.py`, `theme.py`, etc.) are referenced as black-box
dependencies.

## Goal

Rebuild `rich/console.py` — the `Console` class and its in-file helpers —
from scratch using only this spec and a generic Python stdlib + the listed
dependencies. You must **not** copy lines from the source. The output should
behave identically for the checklist in `inventory/functional-checklist.md`.

## Folder map

| Path | Read when you need… |
|---|---|
| `README.md` | High-level overview; what Rich & Console are. |
| `architecture.md` | Quality goals, building blocks, dataflow. |
| `layout/tree.txt` | Repo context (this reverse scope is one file). |
| `layout/src.map.md` | File → purpose, public API, test pointers. |
| `specs/console.spec.md` | **Primary rebuild contract.** Read first. |
| `conventions/code-style.md` | Style rules (black, isort, mypy). |
| `conventions/dev-env.md` | How to run the test/lint suite. |
| `conventions/architecture-rules.md` | Threading, lock, error contract rules. |
| `inventory/functional-checklist.md` | The grading key for rebuild. |

## Reading order

1. `specs/console.spec.md` — the contract.
2. `architecture.md` — to understand the threading + buffer model.
3. `conventions/architecture-rules.md` — to know the invariants.
4. `inventory/functional-checklist.md` — to know what "done" means.

Skip the repo's own source. If the spec is silent on something the checklist
asks for, the original source wins; record the gap and flag it in your
rebuild report.
