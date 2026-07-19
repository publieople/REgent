# REgent

**Reverse any Git repository into a structured natural-language specification.**

Given a Git URL, REgent reads every file, maps the structure, infers the conventions, and emits a structured `spec/` tree that an AI coding agent can read to rebuild — or refactor — the original software from scratch. No code is copied; the reconstruction is done from natural language + a verified functional checklist.

## Two-Step Pipeline

1. **Reverse** — `repo → spec/` (this MVP focus)
2. **Build** — `spec/ → new repo, tests pass` (next milestone)

A third skill, **Refactor**, reuses the same pipeline: reverse → edit `spec/` → build.

## Spec Layout (Draft v0)

```
spec/
├── AGENTS.md                    # Entry point (agents.md standard)
├── README.md                    # Human overview
├── architecture.md              # arc42-style 3-section overview
├── layout/
│   ├── tree.txt                 # Mirrored directory tree
│   └── src.map.md               # File → one-line function
├── specs/                       # OpenSpec-style per-module specs
│   └── <module>.spec.md         # should/must + Scenario blocks
├── conventions/                 # Inferred dev rules
│   ├── code-style.md
│   ├── dev-env.md
│   └── architecture-rules.md
└── inventory/
    └── functional-checklist.md  # Verification baseline
```

## Status

**Phase 1 (reverse) — in progress.** First repository will be reverse-engineered end-to-end before any build step is shipped.

## License

GPL-3.0-or-later. See [LICENSE](./LICENSE).
