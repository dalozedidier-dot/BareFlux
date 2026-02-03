#!/usr/bin/env python3
"""Déduplication d'artefacts zip (ex: dd_graph_artifacts.zip / dd_graph_artifacts (1).zip)

- calcule SHA256
- supprime les doublons exacts
- écrit un rapport JSON

Usage:
  python tools/dedup_artifacts.py --dir . --pattern "dd_graph_artifacts*.zip" --report _bareflux_out/dedup_report.json
"""
from __future__ import annotations
import argparse
import glob
import hashlib
import json
import os
from pathlib import Path

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".")
    ap.add_argument("--pattern", default="dd_graph_artifacts*.zip")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", default="dedup_report.json")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, args.pattern)))
    seen = {}
    actions = []
    for fp in files:
        s = sha256_file(fp)
        if s in seen:
            actions.append({"file": fp, "sha256": s, "duplicate_of": seen[s], "deleted": (not args.dry_run)})
            if not args.dry_run:
                os.remove(fp)
        else:
            seen[s] = fp

    report = {"scanned": files, "unique": list(seen.values()), "actions": actions}
    Path(os.path.dirname(args.report) or ".").mkdir(parents=True, exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("OK unique=", len(seen), "duplicates=", len(actions), "report=", args.report)

if __name__ == "__main__":
    main()
