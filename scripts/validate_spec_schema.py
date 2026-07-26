#!/usr/bin/env python3
"""
Validate that every fixed spec fixture under spec-out/ conforms to REgent's
spec/ tree schema. Emits GitHub Actions annotations so failures show inline
on the PR diff.

Currently treats each spec-out/<fixture>/spec/ directory as a *product* (a
fixed list of named fixtures we care about), not as a general validator — see
`--ponytail` flag to relax to all-of-spec-out scanning when more fixtures
land.

Usage:
    python3 scripts/validate_spec_schema.py            # default: fixed list
    python3 scripts/validate_spec_schema.py --ponytail # scan every dir

Exit codes: 0 = all OK, 1 = at least one fixture missing required schema.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# ponytail: fixed list per user's "treat as product" decision. Add new
# fixtures here as they land. The script does NOT auto-discover to keep the
# gate sharp — a new fixture that nobody reviewed must not silently pass.
FIXTURES: tuple[str, ...] = (
    "reverse-fixture-tiny",
    "rich",
    "ripgrep",
)

REQUIRED_TOP = ("AGENTS.md", "README.md", "architecture.md")
REQUIRED_LAYOUT = ("tree.txt", "src.map.md")
REQUIRED_CONVENTIONS = (
    "code-style.md",
    "dev-env.md",
    "architecture-rules.md",
)
REQUIRED_INVENTORY = ("functional-checklist.md",)
MIN_CHECKLIST_ITEMS = 5  # all 3 current fixtures have 20/59/39; 5 is a floor


def gh_annotate(level: str, path: str, msg: str) -> None:
    """Print a GitHub Actions workflow command. Ignored outside GH Actions."""
    # Escape for the ::message syntax (no \n, no %).
    safe_msg = msg.replace("\n", "%0A").replace(":", "%3A").replace(",", "%2C")
    print(f"::{level} file={path}::{safe_msg}")


def validate_fixture(root: Path, fixture: str) -> list[str]:
    """Return list of human-readable error strings (empty = OK)."""
    errs: list[str] = []
    spec = root / "spec-out" / fixture / "spec"
    if not spec.is_dir():
        return [f"spec-out/{fixture}/spec/ does not exist"]

    # Top-level required files
    for f in REQUIRED_TOP:
        p = spec / f
        if not p.is_file():
            errs.append(f"missing top-level file: {f}")

    # layout/ subtree
    layout = spec / "layout"
    if not layout.is_dir():
        errs.append("missing layout/ directory")
    else:
        for f in REQUIRED_LAYOUT:
            if not (layout / f).is_file():
                errs.append(f"missing layout/{f}")

    # conventions/ subtree
    conv = spec / "conventions"
    if not conv.is_dir():
        errs.append("missing conventions/ directory")
    else:
        for f in REQUIRED_CONVENTIONS:
            if not (conv / f).is_file():
                errs.append(f"missing conventions/{f}")

    # inventory/ subtree
    inv = spec / "inventory"
    if not inv.is_dir():
        errs.append("missing inventory/ directory")
    else:
        for f in REQUIRED_INVENTORY:
            p = inv / f
            if not p.is_file():
                errs.append(f"missing inventory/{f}")
            elif f == "functional-checklist.md":
                # Must actually contain some checkbox items, not just a header.
                try:
                    body = p.read_text(encoding="utf-8")
                except OSError as e:
                    errs.append(f"inventory/{f}: cannot read ({e})")
                    continue
                n = len(re.findall(r"^- \[[ xX]\]", body, re.M))
                if n < MIN_CHECKLIST_ITEMS:
                    errs.append(
                        f"inventory/{f}: only {n} checkbox items, "
                        f"need >= {MIN_CHECKLIST_ITEMS}"
                    )

    # specs/ subtree: at least one *.spec.md
    specs = spec / "specs"
    if not specs.is_dir():
        errs.append("missing specs/ directory")
    else:
        specs_md = [p for p in specs.iterdir() if p.name.endswith(".spec.md")]
        if not specs_md:
            errs.append("specs/: no *.spec.md file found")

    return errs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ponytail",
        action="store_true",
        help="scan every spec-out/*/spec/ directory instead of the fixed list",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="repo root (default: current directory)",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()

    fixtures = FIXTURES
    if args.ponytail:
        out = root / "spec-out"
        if out.is_dir():
            fixtures = tuple(
                sorted(
                    p.name
                    for p in out.iterdir()
                    if (p / "spec").is_dir()
                )
            )

    if not fixtures:
        print("ERROR: no fixtures to validate", file=sys.stderr)
        return 1

    total_errs = 0
    summary_lines: list[str] = ["# REgent spec schema validation", ""]
    for fixture in fixtures:
        errs = validate_fixture(root, fixture)
        rel_spec = f"spec-out/{fixture}/spec"
        if errs:
            total_errs += len(errs)
            print(f"[FAIL] {rel_spec}  ({len(errs)} issue(s))")
            for e in errs:
                print(f"  - {e}")
                gh_annotate("error", rel_spec, e)
            summary_lines.append(f"- ❌ **{fixture}**: {len(errs)} issue(s)")
        else:
            print(f"[ OK ] {rel_spec}")
            summary_lines.append(f"- ✅ **{fixture}**")
    summary_lines.append("")
    summary_lines.append(f"**Total**: {total_errs} issue(s) across {len(fixtures)} fixture(s)")

    # Write job summary so it shows in the Actions UI.
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        Path(summary_file).write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return 1 if total_errs else 0


if __name__ == "__main__":
    sys.exit(main())