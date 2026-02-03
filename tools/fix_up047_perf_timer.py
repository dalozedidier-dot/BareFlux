#!/usr/bin/env python3
"""
Fix Ruff UP047 on common/utils.py (perf_timer):
- Convert standalone TypeVar/ParamSpec generics to PEP 695 function type parameters (Python 3.12+).

Target:
  common/utils.py: def perf_timer(...)

Typical before:
  from typing import ParamSpec, TypeVar
  P = ParamSpec("P")
  R = TypeVar("R")
  def perf_timer(func: Callable[P, R]) -> Callable[P, R]:

After:
  def perf_timer[**P, R](func: Callable[P, R]) -> Callable[P, R]:

And (if adjacent) removes the standalone `P = ParamSpec(...)` and `R = TypeVar(...)` lines,
and removes unused ParamSpec/TypeVar imports if they became unused.

Usage:
  python tools/fix_up047_perf_timer.py
  python tools/fix_up047_perf_timer.py --file common/utils.py
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

DEF_RE = re.compile(r"^(\s*)def\s+perf_timer\s*\(", re.M)

PARAMSPEC_RE = re.compile(r'^\s*(?P<name>_?[A-Z][A-Za-z0-9_]*)\s*=\s*ParamSpec\(\s*["\'](?P=name)["\']\s*\)\s*$', re.M)
TYPEVAR_RE = re.compile(r'^\s*(?P<name>_?[A-Z][A-Za-z0-9_]*)\s*=\s*TypeVar\(\s*["\'](?P=name)["\']', re.M)

def _remove_adjacent_typevars(text: str, def_pos: int, window: int = 20) -> tuple[str, str, str]:
    """
    Try to find ParamSpec + TypeVar definitions immediately above perf_timer within `window` lines.
    Returns (new_text, P_name, R_name) where names default to ("P","R") if not found.
    """
    lines = text.splitlines(True)
    # map char pos -> line index
    char = 0
    def_line_idx = 0
    for i, ln in enumerate(lines):
        if char <= def_pos < char + len(ln):
            def_line_idx = i
            break
        char += len(ln)

    start = max(0, def_line_idx - window)
    block = "".join(lines[start:def_line_idx])

    # Find last ParamSpec/TypeVar defs in block
    P_name = None
    R_name = None
    for m in PARAMSPEC_RE.finditer(block):
        P_name = m.group("name")
    for m in TYPEVAR_RE.finditer(block):
        R_name = m.group("name")

    # If defs exist, remove only if they appear in the last few lines of the block (adjacent-ish).
    if P_name and R_name:
        # remove the specific lines defining them (only once each)
        new_lines = []
        removed_P = removed_R = False
        for i in range(len(lines)):
            ln = lines[i]
            if i < def_line_idx and not removed_P and re.match(rf'^\s*{re.escape(P_name)}\s*=\s*ParamSpec\(', ln):
                removed_P = True
                continue
            if i < def_line_idx and not removed_R and re.match(rf'^\s*{re.escape(R_name)}\s*=\s*TypeVar\(', ln):
                removed_R = True
                continue
            new_lines.append(ln)
        return ("".join(new_lines), P_name, R_name)

    return (text, P_name or "P", R_name or "R")

def _pep695ize_perf_timer(text: str, P_name: str, R_name: str) -> str:
    # Replace "def perf_timer(" with "def perf_timer[**P, R]("
    # Keep indentation.
    def repl(m):
        indent = m.group(1)
        return f"{indent}def perf_timer[**{P_name}, {R_name}]("
    return DEF_RE.sub(repl, text, count=1)

def _cleanup_imports(text: str) -> str:
    # If ParamSpec/TypeVar no longer used, remove them from `from typing import ...` lines.
    uses_paramspec = re.search(r"\bParamSpec\b", text) is not None
    uses_typevar = re.search(r"\bTypeVar\b", text) is not None

    if uses_paramspec or uses_typevar:
        return text

    # Remove ParamSpec/TypeVar from typing imports (basic patterns)
    def fix_import_line(line: str) -> str:
        m = re.match(r"^(\s*)from\s+typing\s+import\s+(.*)$", line)
        if not m:
            return line
        indent, rest = m.group(1), m.group(2)
        # handle parentheses
        rest_stripped = rest.strip()
        if rest_stripped.startswith("(") and rest_stripped.endswith(")"):
            inner = rest_stripped[1:-1]
            parts = [p.strip() for p in inner.split(",") if p.strip()]
            parts = [p for p in parts if p not in ("ParamSpec", "TypeVar")]
            if not parts:
                return ""  # drop whole import
            return indent + "from typing import (" + ", ".join(parts) + ")\n"
        else:
            parts = [p.strip() for p in rest.split(",") if p.strip()]
            parts = [p for p in parts if p not in ("ParamSpec", "TypeVar")]
            if not parts:
                return ""
            return indent + "from typing import " + ", ".join(parts) + "\n"

    lines = text.splitlines(True)
    out = []
    for ln in lines:
        if "from typing import" in ln:
            ln2 = fix_import_line(ln)
            if ln2:
                out.append(ln2)
        else:
            out.append(ln)
    return "".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="common/utils.py")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"file not found: {path}")

    text = path.read_text(encoding="utf-8")

    m = DEF_RE.search(text)
    if not m:
        raise SystemExit("perf_timer definition not found")

    # If already pep695, exit cleanly
    if re.search(r"def\s+perf_timer\s*\[", text):
        print("OK (already PEP 695)")
        return

    text2, P_name, R_name = _remove_adjacent_typevars(text, m.start())
    text3 = _pep695ize_perf_timer(text2, P_name, R_name)
    text4 = _cleanup_imports(text3)

    if text4 == text:
        print("NO CHANGE")
        return

    path.write_text(text4, encoding="utf-8")
    print("OK (patched)", path)

if __name__ == "__main__":
    main()
