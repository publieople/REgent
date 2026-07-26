#!/usr/bin/env python3
"""
Validate every SKILL.md in skills/ against the agentskills.io-conformant
frontmatter REgent expects. Pure stdlib - no PyYAML, works on GitHub
Actions ubuntu-latest runner without setup.

Required (hard error, exit 1):
- file has YAML frontmatter delimited by '---' markers
- the opening '---' is on line 1 and the closing '---' is on its own line
- YAML parses without exceptions
- `name:` field present, short, kebab-case-like
- `description:` field present, non-empty, >= 20 chars

Recommended (warning, not failing):
- `version:` present and looks like semver (X.Y.Z)
- `license:` present and non-empty
- `metadata.hermes.tags` non-empty array (used for skills.sh discovery)

Usage:
    python3 scripts/validate_skill_frontmatter.py [skills/]
Exit codes: 0 = OK or warnings only; 1 = at least one hard error.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


def split_frontmatter(text):
    """Return (yaml, body) or None if no proper frontmatter fenced."""
    if not text.startswith("---\n"):
        return None
    m = re.search(r"\n---\n", text)
    if not m:
        return None
    return text[4:m.start()], text[m.end():]


def _parse_scalar(v, errs, n):
    if v.startswith(chr(34)) and v.endswith(chr(34)):
        return v[1:-1]
    if v.startswith(chr(39)) and v.endswith(chr(39)):
        return v[1:-1]
    return v


def _parse_inline_list(v):
    inside = v[1:-1].strip()
    if not inside:
        return []
    return [s.strip().strip(chr(34)).strip(chr(39)) for s in inside.split(",")]


def parse_simple_yaml(yaml_text):
    """
    Hand-rolled YAML-ish parser for SKILL.md frontmatter. Supports:
      - top-level scalars and dicts
      - 2-level nested dicts (e.g. metadata: { hermes: ... })
      - 3-level nested dicts (e.g. metadata.hermes: { tags: [...] })
    Anything deeper is treated as a flat string and emits a warning-equivalent
    parse error. Returns (root_dict, errors).
    """
    errs = []
    root = {}
    # stack frames describe parent containers keyed by indent level.
    # Each frame: (indent: int, container: dict)
    stack = []  # list of [indent, container]; container[0] is always root
    stack.append([0, root])

    def parent_frame(level):
        while len(stack) > 1 and stack[-1][0] >= level:
            stack.pop()
        return stack[-1]

    for n, line in enumerate(yaml_text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if ":" not in line:
            errs.append(f"line {n}: missing ':' on entry: {line!r}")
            continue
        k, _, v = line.lstrip().partition(":")
        k = k.strip()
        v = v.strip()
        frame = parent_frame(indent)
        container = frame[1]
        if indent <= frame[0]:
            container = frame[1]
        if v == "":
            new = {}
            container[k] = new
            stack.append([indent, new])
        elif v.startswith("[") and v.endswith("]"):
            container[k] = _parse_inline_list(v)
        else:
            container[k] = _parse_scalar(v, errs, n)
    # any leftover stack frames (besides root) auto-flush as already inserted
    return root, errs


def gh_annotate(level, path, msg):
    safe = msg.replace("\n", "%0A").replace(":", "%3A").replace(",", "%2C")
    print(f"::{level} file={path}::{safe}")


def _dig(d, *path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def validate_one(path):
    errors = []
    warnings = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"cannot read file: {e}"], []

    fm = split_frontmatter(text)
    if fm is None:
        errors.append(
            "frontmatter missing or malformed "
            "(need leading '---' and a closing '---' on its own line)"
        )
        return errors, warnings

    yaml_text, _body = fm
    parsed, parse_errs = parse_simple_yaml(yaml_text)
    for e in parse_errs:
        errors.append(f"frontmatter parse: {e}")

    name = parsed.get("name")
    if not name:
        errors.append("missing required field: `name:`")
    elif not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", name):
        errors.append(
            "`name:` must be kebab-case (lowercase, digits, hyphens, "
            f"start with letter); got {name!r}"
        )

    desc = parsed.get("description")
    if not desc:
        errors.append("missing required field: `description:`")
    elif len(desc) < 20:
        errors.append(
            f"`description:` too short ({len(desc)} chars); agentskills.io "
            f"recommends >= 20 chars (this is the field skills.sh indexes "
            f"for search and trigger)"
        )

    version = parsed.get("version")
    if not version:
        warnings.append("missing recommended field: `version:`")
    elif not re.fullmatch(r"\d+(\.\d+){1,3}(\.\w+)?", str(version)):
        warnings.append(
            "`version:` should look like semver (e.g. '1.2.0' or "
            f"'1.2.0.beta'); got {version!r}"
        )

    license_ = parsed.get("license")
    if not license_:
        warnings.append("missing recommended field: `license:`")

    tags = _dig(parsed, "metadata", "hermes", "tags")
    if not tags:
        warnings.append(
            "metadata.hermes.tags is empty or missing (kills skills.sh discovery)"
        )

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skills_dir",
        nargs="?",
        default="skills",
        help="directory to walk (default: skills/)",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="exit 1 on warnings too",
    )
    args = parser.parse_args()
    root = Path(args.skills_dir).resolve()
    if not root.is_dir():
        print(f"ERROR: {root} is not a directory", file=sys.stderr)
        return 1

    files = sorted(root.rglob("SKILL.md"))
    if not files:
        print("ERROR: no SKILL.md files found", file=sys.stderr)
        return 1

    total_err = 0
    total_warn = 0
    summary_lines = ["# REgent SKILL.md lint", ""]
    cwd = Path.cwd()
    for p in files:
        try:
            rel = p.relative_to(cwd).as_posix()
        except ValueError:
            rel = str(p)
        errs, warns = validate_one(p)
        total_err += len(errs)
        total_warn += len(warns)
        verdict = "FAIL" if errs else ("WARN" if warns else " OK ")
        print(f"[{verdict}] {rel}  (errors={len(errs)}, warnings={len(warns)})")
        for e in errs:
            print(f"  ERROR  {e}")
            gh_annotate("error", rel, e)
        for w in warns:
            print(f"  WARN   {w}")
            gh_annotate("warning", rel, w)
        glyph = chr(10060) if errs else (chr(9888) + chr(65039) if warns else chr(9989))
        line = f"- {glyph} **{rel}** - {len(errs)} error(s), {len(warns)} warning(s)"
        summary_lines.append(line)
    summary_lines.append("")
    summary_lines.append(
        f"**Total**: {total_err} error(s), {total_warn} warning(s) "
        f"across {len(files)} SKILL.md file(s)"
    )

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        Path(summary_file).write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    if total_err:
        return 1
    if args.fail_on_warnings and total_warn:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
