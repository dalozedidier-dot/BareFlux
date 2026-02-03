#!/usr/bin/env python3
"""
RiftLens sweep report: agrège des graph_report.json sur plusieurs seuils.
- n_nodes / n_edges par seuil
- top-3 edges par poids (si disponible)

Entrée: dossier run_*/.../thr_*/graph_report.json
Usage:
  python tools/riftlens_sweep_report.py --root riftlens_mass --out_csv _bareflux_out/riftlens_sweep.csv --out_json _bareflux_out/riftlens_sweep.json
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os


def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def edge_top3(edges):
    parsed = []
    for e in edges or []:
        if isinstance(e, dict):
            w = e.get("weight", e.get("w", 0.0))
            u = e.get("source", e.get("u", e.get("a", "")))
            v = e.get("target", e.get("v", e.get("b", "")))
        elif isinstance(e, (list, tuple)) and len(e) >= 2:
            u, v = e[0], e[1]
            w = e[2] if len(e) >= 3 else 0.0
        else:
            continue
        parsed.append((float(w), str(u), str(v)))
    parsed.sort(reverse=True, key=lambda t: t[0])
    return [{"weight": w, "u": u, "v": v} for (w, u, v) in parsed[:3]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out_csv", default="riftlens_sweep.csv")
    ap.add_argument("--out_json", default="riftlens_sweep.json")
    args = ap.parse_args()

    files = glob.glob(os.path.join(args.root, "run_*", "**", "graph_report.json"), recursive=True)
    rows = []
    for fp in files:
        if "thr_" not in fp:
            continue
        parts = fp.split(os.sep)
        run = next((p for p in parts if p.startswith("run_")), "run_unknown")
        thr = next((p for p in parts if p.startswith("thr_")), "thr_unknown").replace("thr_", "")
        gr = load_json(fp)
        rows.append({
            "run": run,
            "threshold": thr,
            "n_nodes": gr.get("n_nodes"),
            "n_edges": gr.get("n_edges"),
            "top3_edges": json.dumps(edge_top3(gr.get("edges", []))),
        })

    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["run", "threshold", "n_nodes", "n_edges", "top3_edges"])
        w.writeheader()
        w.writerows(rows)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "n_files": len(rows)}, f, indent=2)

    print("OK", args.out_csv, args.out_json)


if __name__ == "__main__":
    main()
