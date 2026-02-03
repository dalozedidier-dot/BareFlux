#!/usr/bin/env python3
"""
Génère un mini-rapport Markdown (README/article) à partir des fichiers stats disponibles.

Usage:
  python examples/make_report_md.py --path . --out bareflux_report.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=".", help="Dossier où se trouvent les fichiers stats.")
    ap.add_argument("--out", default="bareflux_report.md")
    args = ap.parse_args()

    base = Path(args.path)
    outp = Path(args.out)

    b_mean = b_entropy = a_entropy = None
    b_q75 = None
    t_share = None

    # Shadow diff
    csv_path = base / "bareflux_shadow_diff_stats.csv"
    if csv_path.exists():
        import pandas as pd  # dependency
        df = pd.read_csv(csv_path)
        if "column" in df.columns:
            def row(col):
                r = df[df["column"] == col]
                return None if r.empty else r.iloc[0]
            rb = row("b")
            ra = row("a")
            rt = row("t")
            if rb is not None:
                b_mean = float(rb.get("mean", 0.0))
                b_entropy = float(rb.get("entropy_bits", 0.0))
                if "q75" in rb.index:
                    b_q75 = float(rb.get("q75"))
            if ra is not None:
                a_entropy = float(ra.get("entropy_bits", 0.0)) if "entropy_bits" in ra.index else None
            if rt is not None and "share_nonzero" in rt.index:
                t_share = float(rt.get("share_nonzero", 0.0))

    # RiftLens
    rl_nodes = rl_edges = rl_edgew = None
    rift_path = base / "riftlens_by_threshold.csv"
    if rift_path.exists():
        import pandas as pd  # dependency
        df = pd.read_csv(rift_path)
        if "nodes_mean" in df.columns:
            rl_nodes = float(df["nodes_mean"].mean())
        if "edges_mean" in df.columns:
            rl_edges = float(df["edges_mean"].mean())
        if "edgew_mean" in df.columns:
            rl_edgew = float(df["edgew_mean"].mean())

    # VoidMark global
    vm_mean_of_means = vm_entropy = None
    vm_path = base / "voidmark_global.json"
    if vm_path.exists():
        with open(vm_path, "r", encoding="utf-8") as f:
            g = json.load(f)
        vm_mean_of_means = g.get("mean_of_means")
        vm_entropy = g.get("mean_entropy_bits")

    md = []
    md.append("## Résultats clés BareFlux")
    md.append("")
    md.append("### Shadow Diff")
    if b_mean is not None:
        line = f"- **Colonne b** : mean delta = **{b_mean:+.4f}**"
        if b_q75 is not None:
            line += f", q75 = **{b_q75:+.4f}**"
        if b_entropy is not None:
            line += f", entropie **{b_entropy:.2f} bits**"
        md.append(line)
    if a_entropy is not None:
        md.append(f"- **Colonne a** : entropie **{a_entropy:.2f} bits**")
    if t_share is not None:
        md.append(f"- **Colonne t** : share_nonzero = **{t_share:.1%}**")
    md.append("")
    md.append("### RiftLens")
    if rl_nodes is not None and rl_edges is not None:
        md.append(f"- Moyennes sur seuils : **{rl_nodes:.1f} nœuds**, **{rl_edges:.1f} arêtes**")
    if rl_edgew is not None:
        md.append(f"- Poids moyen des arêtes : **{rl_edgew:.5f}**")
    md.append("")
    md.append("### VoidMark")
    if vm_mean_of_means is not None:
        md.append(f"- Mean of means : **{float(vm_mean_of_means):+.4f}**")
    if vm_entropy is not None:
        md.append(f"- Entropie moyenne : **{float(vm_entropy):.3f} bits**")
    md.append("")

    outp.write_text("\n".join(md), encoding="utf-8")
    print("OK", str(outp))


if __name__ == "__main__":
    main()
