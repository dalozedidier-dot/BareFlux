#!/usr/bin/env python3
"""
BareFlux post-process (low-hanging fruit)
- Fix n_edges incohérence en recopiant la valeur depuis riftlens/graph_report.json vers le summary
- Ajoute score global de dérive + statut CI (green/yellow/red)
- Ajoute métriques lisibilité colonne b (IQR/MAD + % outliers)

Usage:
  python tools/bareflux_postprocess.py --out _bareflux_out --inplace
  python tools/bareflux_postprocess.py --out _bareflux_out --inplace --skip-if-missing

Hypothèses minimales:
  - _bareflux_out/**/shadow_diff.json existe
  - _bareflux_out/riftlens/graph_report.json existe (sinon n_edges non patchable)
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
from pathlib import Path
from statistics import mean, pstdev


def quantile(sorted_vals, q: float) -> float:
    if not sorted_vals:
        return float("nan")
    if q <= 0:
        return float(sorted_vals[0])
    if q >= 1:
        return float(sorted_vals[-1])
    pos = (len(sorted_vals) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_vals[lo])
    frac = pos - lo
    return float(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac)


def mad(vals):
    if not vals:
        return float("nan")
    s = sorted(vals)
    med = quantile(s, 0.5)
    dev = [abs(v - med) for v in vals]
    return quantile(sorted(dev), 0.5)


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, obj):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def find_one(patterns):
    for pat in patterns:
        hits = glob.glob(pat, recursive=True)
        if hits:
            hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return hits[0]
    return None


def extract_deltas(shadow_diff, col: str):
    try:
        d = shadow_diff["diff"]["column_changes"][col]["deltas"]
        vals = [float(v) for v in d.values()]
        return vals
    except Exception:
        return []


def compute_stats(vals):
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    mu = mean(vals)
    sd = pstdev(vals) if len(vals) > 1 else 0.0
    q05 = quantile(s, 0.05)
    q25 = quantile(s, 0.25)
    q50 = quantile(s, 0.50)
    q75 = quantile(s, 0.75)
    q95 = quantile(s, 0.95)
    mad_v = mad(vals)
    iqr_v = q75 - q25
    return {
        "n": len(vals),
        "mean": mu,
        "std": sd,
        "q05": q05,
        "q25": q25,
        "q50": q50,
        "q75": q75,
        "q95": q95,
        "mad": mad_v,
        "iqr": iqr_v,
        "iqr_over_mad": (iqr_v / mad_v) if (mad_v and not math.isnan(mad_v) and mad_v != 0) else None,
        "min": s[0],
        "max": s[-1],
    }


def effective_drift(stats_a, stats_b):
    # dérive effective = max(|mean_a|, |mean_b|) + 0.5*(q95_b - q05_b)
    if not stats_a or not stats_b or stats_a.get("n", 0) == 0 or stats_b.get("n", 0) == 0:
        return None
    term1 = max(abs(stats_a.get("mean", 0.0)), abs(stats_b.get("mean", 0.0)))
    term2 = 0.5 * (stats_b.get("q95", 0.0) - stats_b.get("q05", 0.0))
    return float(term1 + term2)


def colorize(score, green_max, yellow_max):
    if score is None or math.isnan(score):
        return "unknown"
    if score <= green_max:
        return "green"
    if score <= yellow_max:
        return "yellow"
    return "red"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_bareflux_out", help="Output directory produced by bareflux orchestrate")
    ap.add_argument("--config", default="tools/config_score.json", help="Config JSON (thresholds, etc.)")
    ap.add_argument("--inplace", action="store_true", help="Overwrite summary file if exists (default: write patched copy)")
    ap.add_argument("--skip-if-missing", action="store_true", help="Exit 0 (status=skipped) if required inputs are missing")
    args = ap.parse_args()

    out_dir = args.out
    cfg = load_json(args.config) if os.path.exists(args.config) else {}
    thr = cfg.get("thresholds", {})
    green_max = float(thr.get("green_max", 0.20))
    yellow_max = float(thr.get("yellow_max", 0.50))
    b_thr = cfg.get("b_outlier_thresholds", [0.05, 0.10, 0.20])

    shadow_diff_path = find_one([os.path.join(out_dir, "**", "shadow_diff.json")])
    if not shadow_diff_path:
        if args.skip_if_missing:
            ci_status_path = os.path.join(out_dir, "bareflux_ci_status.json")
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            write_json(ci_status_path, {"status": "skipped_missing_shadow_diff", "out_dir": out_dir})
            print("SKIPPED: shadow_diff.json missing")
            return
        raise SystemExit(f"shadow_diff.json introuvable sous {out_dir}")

    shadow = load_json(shadow_diff_path)

    stats = {}
    for col in ("a", "b", "t"):
        vals = extract_deltas(shadow, col)
        stats[col] = compute_stats(vals)

    # b readability
    b_vals = extract_deltas(shadow, "b")
    b_read = {
        "n": len(b_vals),
        "thresholds": {},
        "iqr": stats["b"].get("iqr"),
        "mad": stats["b"].get("mad"),
        "iqr_over_mad": stats["b"].get("iqr_over_mad"),
    }
    if b_vals:
        for th in b_thr:
            pct = sum(1 for v in b_vals if abs(v) > float(th)) / len(b_vals)
            b_read["thresholds"][str(th)] = {"pct_abs_gt": pct}

    # graph_report (n_edges fix)
    graph_report_path = os.path.join(out_dir, "riftlens", "graph_report.json")
    graph = load_json(graph_report_path) if os.path.exists(graph_report_path) else None

    summary_path = find_one([
        os.path.join(out_dir, "**", "*orchestration_summary*.json"),
        os.path.join(out_dir, "**", "*summary*.json"),
    ])
    summary = load_json(summary_path) if summary_path else {}

    if graph is not None:
        summary.setdefault("riftlens", {})
        summary["riftlens"]["n_nodes"] = graph.get("n_nodes", summary["riftlens"].get("n_nodes"))
        summary["riftlens"]["n_edges"] = graph.get("n_edges", summary["riftlens"].get("n_edges"))

    score = effective_drift(stats["a"], stats["b"])
    status = colorize(score, green_max, yellow_max)

    summary.setdefault("drift", {})
    summary["drift"]["score_effective_v1"] = score
    summary["drift"]["status"] = status
    summary["drift"]["thresholds"] = {"green_max": green_max, "yellow_max": yellow_max}

    summary.setdefault("shadow_diff", {})
    summary["shadow_diff"]["columns"] = {"a": stats["a"], "b": stats["b"], "t": stats["t"]}
    summary["shadow_diff"]["b_readability"] = b_read

    ci_status = {"score_effective_v1": score, "status": status, "thresholds": {"green_max": green_max, "yellow_max": yellow_max}}
    b_read_path = os.path.join(out_dir, "bareflux_column_b_readability.json")
    ci_status_path = os.path.join(out_dir, "bareflux_ci_status.json")

    if summary_path and args.inplace:
        out_summary = summary_path
    elif summary_path:
        out_summary = summary_path.replace(".json", ".patched.json")
    else:
        out_summary = os.path.join(out_dir, "bareflux_orchestration_summary.patched.json")

    write_json(out_summary, summary)
    write_json(ci_status_path, ci_status)
    write_json(b_read_path, b_read)

    print("OK")
    print(f"- shadow_diff: {shadow_diff_path}")
    print(f"- graph_report: {graph_report_path if graph else 'n/a'}")
    print(f"- summary_out: {out_summary}")
    print(f"- ci_status: {ci_status_path}")
    print(f"- b_readability: {b_read_path}")


if __name__ == "__main__":
    main()
