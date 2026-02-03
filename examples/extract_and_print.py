#!/usr/bin/env python3
"""
Exemples concrets et prêts à l'emploi pour:
  - Shadow diff (BareFlux / bloc4)
  - RiftLens (stabilité par seuil)
  - VoidMark (robustesse au bruit)
  - Score composite (simple)

Usage (dossier courant contenant les fichiers):
  python examples/extract_and_print.py

Usage (chemin explicite):
  python examples/extract_and_print.py --path _bareflux_out

Fichiers attendus (si présents):
  - bareflux_shadow_diff_stats.csv
  - bloc4_shadow_diff_stats.csv
  - riftlens_by_threshold.csv
  - voidmark_run_stats.csv
  - voidmark_global.json
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def _p(base: str, name: str) -> str:
    return str(Path(base) / name)


def _exists(path: str) -> bool:
    return Path(path).exists()


def part1_shadow_diff(base: str) -> None:
    import pandas as pd  # dependency

    f_bare = _p(base, "bareflux_shadow_diff_stats.csv")
    f_bloc = _p(base, "bloc4_shadow_diff_stats.csv")

    if not _exists(f_bare):
        print(f"[shadow diff] fichier manquant: {f_bare}")
        return

    df_bare = pd.read_csv(f_bare)
    print("=== Stats shadow diff (BareFlux) ===")
    if "column" not in df_bare.columns:
        print("CSV inattendu: colonne 'column' absente")
        return

    b_row = df_bare[df_bare["column"] == "b"]
    if b_row.empty:
        print("Colonne 'b' absente du CSV")
        return
    b = b_row.iloc[0]

    def g(key, default=None):
        return b[key] if key in b.index else default

    n = int(g("n", 0) or 0)
    nz = int(g("n_nonzero", 0) or 0)
    share = float(g("share_nonzero", 0.0) or 0.0)

    print("Colonne b:")
    print(f"  Non-zéros         : {nz} / {n} ({share:.1%})")
    print(f"  Moyenne delta     : {float(g('mean', 0.0)):+.6f}")
    if "median" in b.index:
        print(f"  Médiane           : {float(g('median')):+.6f}")
    if "mad" in b.index:
        print(f"  MAD (robust)      : {float(g('mad')):.2e}")
    if all(k in b.index for k in ["q05", "q25", "q75", "q95"]):
        print(
            "  Quantiles clés    : "
            f"q05 = {float(g('q05')):+.4f} | q25 = {float(g('q25')):+.4f} | "
            f"q75 = {float(g('q75')):+.4f} | q95 = {float(g('q95')):+.4f}"
        )
    if all(k in b.index for k in ["min", "max"]):
        print(f"  Extrêmes          : min = {float(g('min')):+.4f} | max = {float(g('max')):+.4f}")
    if "entropy_bits" in b.index:
        print(f"  Entropie discrète : {float(g('entropy_bits')):.3f} bits")

    if _exists(f_bloc):
        df_bloc = pd.read_csv(f_bloc)
        b2 = df_bloc[df_bloc["column"] == "b"].iloc[0]
        diff_mean = abs(float(b2.get("mean", 0.0)) - float(g("mean", 0.0)))
        print(f"
Différence mean bare vs bloc4 sur b : {diff_mean:.2e} → quasi identique")
    print()


def part2_riftlens(base: str) -> None:
    import pandas as pd  # dependency

    f = _p(base, "riftlens_by_threshold.csv")
    if not _exists(f):
        print(f"[riftlens] fichier manquant: {f}")
        return

    df = pd.read_csv(f)
    cols = ["thr", "nodes_mean", "nodes_std", "edges_mean", "edges_std", "edges_p50", "edgew_mean"]

    print("=== Stabilité RiftLens par seuil ===")
    missing = [c for c in cols if c not in df.columns]
    if missing:
        print("CSV inattendu, colonnes manquantes:", missing)
        print(df.head(5).to_string(index=False))
        return

    print(df[cols].round(4).to_string(index=False))
    print("
Conclusion :")
    if (df["nodes_std"] == 0).all() and (df["edges_std"] == 0).all():
        print("  → nœuds/arêtes invariants sur les seuils présents.")
    print(f"  → edgew_mean moyen: {df['edgew_mean'].mean():.5f}")
    print()


def part3_voidmark(base: str) -> None:
    import pandas as pd  # dependency

    f_stats = _p(base, "voidmark_run_stats.csv")
    f_glob = _p(base, "voidmark_global.json")

    if not _exists(f_stats) or not _exists(f_glob):
        print(f"[voidmark] fichiers manquants: {f_stats} ou {f_glob}")
        return

    df = pd.read_csv(f_stats)
    with open(f_glob, "r", encoding="utf-8") as f:
        glob = json.load(f)

    print("=== Synthèse VoidMark ===")
    print(f"  Nombre de runs           : {glob.get('n_runs')}")
    n_total = glob.get('n_total_values')
    print(f"  Valeurs totales          : {n_total:,}" if isinstance(n_total, int) else f"  Valeurs totales          : {n_total}")
    print(f"  Moyenne des moyennes     : {glob.get('mean_of_means'):+.6f}")
    print(f"  Variance des moyennes    : {glob.get('var_of_means'):.6f}")
    print(f"  Médiane des médianes     : {glob.get('median_of_medians'):+.6f}")
    print(f"  Entropie moyenne par run : {glob.get('mean_entropy_bits'):.3f} bits")

    if "entropy_bits" in df.columns and "run" in df.columns:
        target = float(glob.get("mean_entropy_bits", 0.0))
        idx = (df["entropy_bits"] - target).abs().argsort()[:1]
        closest = df.iloc[idx]
        show = [c for c in ["run", "mean", "std", "median", "entropy_bits"] if c in closest.columns]
        print("
Exemple run représentatif (entropie proche de la moyenne):")
        print(closest[show].to_string(index=False))
    print()


def part4_drift_score(base: str) -> None:
    import pandas as pd  # dependency

    f_bare = _p(base, "bareflux_shadow_diff_stats.csv")
    if not _exists(f_bare):
        return

    df = pd.read_csv(f_bare)

    def drift_score(row):
        if row.get("column") == "t":
            return 0.0
        mean_abs = abs(float(row.get("mean", 0.0)))
        spread = float(row.get("q95", 0.0)) - float(row.get("q05", 0.0))
        entropy = float(row.get("entropy_bits", 0.0))
        entropy_norm = entropy / 8.0  # borne grossière
        return round(0.5 * mean_abs + 0.3 * spread + 0.2 * entropy_norm, 4)

    df["drift_score"] = df.apply(drift_score, axis=1)
    cols = [c for c in ["column", "mean", "q95", "q05", "entropy_bits", "drift_score"] if c in df.columns]

    print("=== Score composite de dérive (simple) ===")
    print(df[cols].sort_values("drift_score", ascending=False).to_string(index=False))
    print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=".", help="Dossier contenant les CSV/JSON (ou _bareflux_out).")
    args = ap.parse_args()

    base = args.path
    part1_shadow_diff(base)
    part2_riftlens(base)
    part3_voidmark(base)
    part4_drift_score(base)


if __name__ == "__main__":
    main()
