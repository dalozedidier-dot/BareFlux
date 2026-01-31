from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path

def main() -> None:
    ap = argparse.ArgumentParser(description="Génère des CSV synthétiques (stdlib only) pour bloc 4.")
    ap.add_argument("--out-dir", default="_ci_out/datasets")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    n = int(args.n)
    random.seed(int(args.seed))
    mid = n // 2

    # multi.csv: t,x,y,z (y corrélé puis décorrélé)
    rows = []
    for t in range(n):
        x = random.gauss(0.0, 1.0)
        if t < mid:
            y = x + random.gauss(0.0, 0.1)
        else:
            y = random.gauss(0.0, 1.0)
        z = random.gauss(0.0, 1.0)
        rows.append((t, x, y, z))

    with (out / "multi.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t", "x", "y", "z"])
        w.writerows(rows)

    # previous/current for NullTrace: shift+scale after mid
    prev_rows = []
    curr_rows = []
    for t in range(n):
        a = random.gauss(0.0, 1.0)
        b = random.gauss(0.0, 1.0)
        prev_rows.append((t, a, b))
        if t < mid:
            curr_rows.append((t, a, b))
        else:
            curr_rows.append((t, a + 0.25, b * 1.10))

    with (out / "previous_shadow.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["t", "a", "b"]); w.writerows(prev_rows)
    with (out / "current.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["t", "a", "b"]); w.writerows(curr_rows)

    print(f"datasets_written={out.resolve()}")

if __name__ == "__main__":
    main()
