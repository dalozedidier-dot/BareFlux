#!/usr/bin/env python3
"""
Advanced (optional): outlier flagging sur deltas b via IsolationForest.
- Ne casse pas si scikit-learn absent (status=skipped_no_sklearn)

Usage:
  python tools/advanced_outliers_iforest.py --shadow "_bareflux_out/**/shadow_diff.json" --out _bareflux_out/b_outliers_iforest.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os


def find_one(patterns):
    for pat in patterns:
        hits = glob.glob(pat, recursive=True)
        if hits:
            hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return hits[0]
    return None


def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shadow", default="_bareflux_out/**/shadow_diff.json")
    ap.add_argument("--out", default="_bareflux_out/b_outliers_iforest.json")
    ap.add_argument("--contamination", type=float, default=0.02)
    args = ap.parse_args()

    shadow_path = find_one([args.shadow])
    if not shadow_path:
        raise SystemExit("shadow_diff.json introuvable")

    sd = load_json(shadow_path)
    try:
        d = sd["diff"]["column_changes"]["b"]["deltas"]
        vals = [float(v) for v in d.values()]
        idx = list(d.keys())
    except Exception:
        vals, idx = [], []

    rep = {"shadow_diff": shadow_path, "n": len(vals), "status": "ok", "outliers": []}

    try:
        from sklearn.ensemble import IsolationForest  # type: ignore
    except Exception:
        rep["status"] = "skipped_no_sklearn"
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2)
        print("SKIPPED (no sklearn)")
        return

    if not vals:
        rep["status"] = "no_data"
    else:
        X = [[v] for v in vals]
        model = IsolationForest(contamination=args.contamination, random_state=0)
        pred = model.fit_predict(X)  # -1 outlier
        out = []
        for i, p in enumerate(pred):
            if p == -1:
                out.append({"row": idx[i], "delta_b": vals[i]})
        rep["outliers"] = out
        rep["n_outliers"] = len(out)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)

    print("OK", args.out)


if __name__ == "__main__":
    main()
