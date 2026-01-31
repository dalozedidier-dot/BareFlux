from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

def main() -> None:
    p = argparse.ArgumentParser(description="Génère des CSV synthétiques (bloc 4) pour tests de stabilité.")
    p.add_argument("--out-dir", type=str, default="_ci_out/datasets", help="Dossier de sortie")
    p.add_argument("--n", type=int, default=200, help="Nombre de lignes")
    p.add_argument("--seed", type=int, default=42, help="Seed RNG")
    args = p.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    n = int(args.n)

    # Dataset multi (RiftLens) : corrélation puis rupture
    t = np.arange(n)
    x = rng.normal(0, 1, size=n)
    y = x + rng.normal(0, 0.1, size=n)  # corrélé
    z = rng.normal(0, 1, size=n)
    mid = n // 2
    y[mid:] = rng.normal(0, 1, size=n - mid)  # rupture: décorrélation

    df_multi = pd.DataFrame({"t": t, "x": x, "y": y, "z": z})
    df_multi.to_csv(out / "multi.csv", index=False)

    # NullTrace previous/current : rupture contrôlée
    base = pd.DataFrame({"t": t, "a": rng.normal(0, 1, size=n), "b": rng.normal(0, 1, size=n)})
    prev = base.copy()
    curr = base.copy()
    curr.loc[mid:, "a"] = curr.loc[mid:, "a"] + 0.25
    curr.loc[mid:, "b"] = curr.loc[mid:, "b"] * 1.10

    prev.to_csv(out / "previous_shadow.csv", index=False)
    curr.to_csv(out / "current.csv", index=False)

    print(f"datasets_written={out.resolve()}")

if __name__ == "__main__":
    main()
