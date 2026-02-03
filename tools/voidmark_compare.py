#!/usr/bin/env python3
"""
Compare deux distributions 1D (prev vs curr) avec distances + stats.
Entrées: 2 fichiers JSON contenant une liste de nombres.
Sortie: JSON.

Usage:
  python tools/voidmark_compare.py --prev prev.json --curr curr.json --out report.json
"""
from __future__ import annotations

import argparse
import json
from statistics import mean, pstdev

from distances import wasserstein_1d, energy_distance


def load_list(path):
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, list):
        raise ValueError("JSON doit être une liste")
    return [float(v) for v in obj]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", required=True)
    ap.add_argument("--curr", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    a = load_list(args.prev)
    b = load_list(args.curr)

    rep = {
        "prev": {"n": len(a), "mean": mean(a) if a else None, "std": pstdev(a) if len(a) > 1 else 0.0},
        "curr": {"n": len(b), "mean": mean(b) if b else None, "std": pstdev(b) if len(b) > 1 else 0.0},
        "distances": {"wasserstein_1d": wasserstein_1d(a, b), "energy": energy_distance(a, b)},
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)

    print("OK", args.out)


if __name__ == "__main__":
    main()
