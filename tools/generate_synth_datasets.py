from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path

def _gauss() -> float:
    return random.gauss(0.0, 1.0)

def main() -> None:
    ap = argparse.ArgumentParser(description="Génère des CSV synthétiques (bloc 4) avec corrélations globales non nulles.")
    ap.add_argument("--out-dir", default="_ci_out/datasets")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    n = int(args.n)
    random.seed(int(args.seed))

    # --- Objectif ---
    # Produire un multi.csv où certaines paires franchissent des seuils corr-threshold usuels.
    # Pour y = x + sigma*eps, corr(x,y) ~= 1/sqrt(1+sigma^2).
    # sigma choisis pour approx : 0.85, 0.65, 0.55
    sig_high = 0.62   # corr ~0.85
    sig_mid  = 1.17   # corr ~0.65
    sig_low  = 1.52   # corr ~0.55

    rows = []
    for t in range(n):
        x = _gauss()
        y_high = x + sig_high * _gauss()
        y_mid  = x + sig_mid  * _gauss()
        y_low  = x + sig_low  * _gauss()
        z = _gauss()
        rows.append((t, x, y_high, y_mid, y_low, z))

    with (out / "multi.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t", "x", "y_high", "y_mid", "y_low", "z"])
        w.writerows(rows)

    # --- NullTrace previous/current : rupture contrôlée ---
    mid = n // 2
    prev_rows = []
    curr_rows = []
    for t in range(n):
        a = _gauss()
        b = _gauss()
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
