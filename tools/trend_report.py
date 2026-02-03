#!/usr/bin/env python3
"""
Convertit un history JSONL en CSV de tendances.
Usage:
  python tools/trend_report.py --history .bareflux_history.jsonl --out _bareflux_out/bareflux_trend.csv
"""
from __future__ import annotations

import argparse
import csv
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", default=".bareflux_history.jsonl")
    ap.add_argument("--out", default="bareflux_trend.csv")
    args = ap.parse_args()

    rows = []
    with open(args.history, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    keys = ["ts_utc", "score", "status", "mean_b", "std_b", "n_nodes", "n_edges"]

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in keys})

    print("OK", args.out, "n=", len(rows))


if __name__ == "__main__":
    main()
