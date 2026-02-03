#!/usr/bin/env python3
"""
Append un point de monitoring dans un history JSONL.
Usage:
  python tools/store_history.py --out _bareflux_out --history .bareflux_history.jsonl --keep 10
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from pathlib import Path
from statistics import mean, pstdev


def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def find_one(patterns):
    for pat in patterns:
        hits = glob.glob(pat, recursive=True)
        if hits:
            hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return hits[0]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_bareflux_out")
    ap.add_argument("--history", default=".bareflux_history.jsonl")
    ap.add_argument("--keep", type=int, default=10)
    args = ap.parse_args()

    out_dir = args.out

    ci = {}
    ci_path = os.path.join(out_dir, "bareflux_ci_status.json")
    if os.path.exists(ci_path):
        ci = load_json(ci_path)

    graph = {}
    gr_path = os.path.join(out_dir, "riftlens", "graph_report.json")
    if os.path.exists(gr_path):
        graph = load_json(gr_path)

    shadow_path = find_one([os.path.join(out_dir, "**", "shadow_diff.json")])
    mean_b = None
    std_b = None
    if shadow_path:
        sd = load_json(shadow_path)
        try:
            d = sd["diff"]["column_changes"]["b"]["deltas"]
            vals = [float(v) for v in d.values()]
            mean_b = mean(vals) if vals else None
            std_b = pstdev(vals) if len(vals) > 1 else 0.0
        except Exception:
            pass

    point = {
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "score": ci.get("score_effective_v1"),
        "status": ci.get("status"),
        "mean_b": mean_b,
        "std_b": std_b,
        "n_nodes": graph.get("n_nodes"),
        "n_edges": graph.get("n_edges"),
    }

    Path(os.path.dirname(args.history) or ".").mkdir(parents=True, exist_ok=True)

    with open(args.history, "a", encoding="utf-8") as f:
        f.write(json.dumps(point) + "
")

    with open(args.history, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    if len(lines) > args.keep:
        lines = lines[-args.keep:]
        with open(args.history, "w", encoding="utf-8") as f:
            f.write("
".join(lines) + "
")

    print("OK", args.history, "n=", len(lines))


if __name__ == "__main__":
    main()
