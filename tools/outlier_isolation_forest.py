#!/usr/bin/env python3
"""Outlier detection (advanced): IsolationForest sur deltas b.

Usage:
  python tools/outlier_isolation_forest.py --shadow _bareflux_out/**/shadow_diff.json --out _bareflux_out/outliers.json

Dépendance:
  pip install scikit-learn
"""
from __future__ import annotations
import argparse, json, glob, os

def find_one(patterns):
    for pat in patterns:
        hits = glob.glob(pat, recursive=True)
        if hits:
            hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return hits[0]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shadow", default="_bareflux_out/**/shadow_diff.json")
    ap.add_argument("--out", default="_bareflux_out/outliers.json")
    ap.add_argument("--contamination", type=float, default=0.025)
    args = ap.parse_args()

    path = find_one([args.shadow])
    if not path:
        raise SystemExit("shadow_diff.json introuvable")

    with open(path,"r",encoding="utf-8") as f:
        sd=json.load(f)
    d=sd["diff"]["column_changes"]["b"]["deltas"]
    # shape (n,1)
    X=[[float(v)] for v in d.values()]

    try:
        from sklearn.ensemble import IsolationForest
    except Exception as e:
        raise SystemExit("scikit-learn requis (pip install scikit-learn)") from e

    model=IsolationForest(contamination=args.contamination, random_state=0)
    y=model.fit_predict(X)  # -1 outlier
    out_idx=[i for i,yy in enumerate(y) if yy==-1]

    rep={"n":len(X),"n_outliers":len(out_idx),"contamination":args.contamination,"outlier_indices":out_idx}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(rep,f,indent=2)
    print("OK",args.out)

if __name__=="__main__":
    main()
