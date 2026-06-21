from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def corr(a: np.ndarray, b: np.ndarray) -> float:
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 3:
        return 0.0
    return float(np.corrcoef(a[mask], b[mask])[0, 1])


def write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def scenario_frame(
    n: int, seed: int, scenario: str
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    mid = n // 2
    x = rng.normal(0, 1, n)
    y = x + rng.normal(0, 0.10, n)
    z = rng.normal(0, 1, n)
    a = rng.normal(0, 1, n)
    b = rng.normal(0, 1, n)

    expected_signal = "stable"
    severity = 0.0

    if scenario == "null_stable":
        pass
    elif scenario == "noise_low":
        y = y + rng.normal(0, 0.15, n)
        severity = 0.15
    elif scenario == "noise_high":
        y = y + rng.normal(0, 0.60, n)
        severity = 0.60
    elif scenario == "missing_5pct":
        mask = rng.choice(n, size=max(1, int(0.05 * n)), replace=False)
        y[mask] = np.nan
        severity = 0.05
    elif scenario == "outliers_2pct":
        mask = rng.choice(n, size=max(1, int(0.02 * n)), replace=False)
        y[mask] = y[mask] + rng.normal(6, 1, size=len(mask))
        severity = 0.02
    elif scenario == "weak_shift":
        y[mid:] = y[mid:] + 0.25
        a[mid:] = a[mid:] + 0.25
        expected_signal = "weak_shift"
        severity = 0.25
    elif scenario == "strong_shift":
        y[mid:] = rng.normal(0, 1, n - mid)
        a[mid:] = a[mid:] + 1.00
        b[mid:] = b[mid:] * 1.50
        expected_signal = "strong_shift"
        severity = 1.00
    elif scenario == "correlation_break":
        y[mid:] = rng.normal(0, 1, n - mid)
        expected_signal = "correlation_break"
        severity = 1.00
    else:
        raise ValueError(f"unknown scenario: {scenario}")

    multi = pd.DataFrame({"t": t, "x": x, "y": y, "z": z})
    prev = pd.DataFrame({"t": t, "a": a, "b": b})
    curr = prev.copy()
    if expected_signal != "stable":
        curr.loc[mid:, "a"] = curr.loc[mid:, "a"] + severity
        curr.loc[mid:, "b"] = curr.loc[mid:, "b"] * (1.0 + min(severity, 1.0) / 2.0)

    meta = {
        "scenario": scenario,
        "expected_signal": expected_signal,
        "severity": severity,
        "n": n,
        "seed": seed,
        "corr_xy_first_half": corr(x[:mid], y[:mid]),
        "corr_xy_second_half": corr(x[mid:], y[mid:]),
        "mean_shift_a": float(
            curr["a"].iloc[mid:].mean() - prev["a"].iloc[mid:].mean()
        ),
    }
    return (multi, prev, curr), meta


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate BareFlux robustness stress datasets and truth metadata."
    )
    parser.add_argument("--out-dir", default="_ci_out/robustness")
    parser.add_argument("--n", type=int, default=240)
    parser.add_argument("--seed", type=int, default=7000)
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scenarios = [
        "null_stable",
        "noise_low",
        "noise_high",
        "missing_5pct",
        "outliers_2pct",
        "weak_shift",
        "strong_shift",
        "correlation_break",
    ]

    rows: list[dict[str, Any]] = []
    for i, scenario in enumerate(scenarios):
        frames, meta = scenario_frame(args.n, args.seed + i, scenario)
        multi, prev, curr = frames
        scenario_dir = out / scenario
        write_csv(scenario_dir / "multi.csv", multi)
        write_csv(scenario_dir / "previous_shadow.csv", prev)
        write_csv(scenario_dir / "current.csv", curr)
        (scenario_dir / "truth.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        rows.append(meta | {"path": str(scenario_dir)})

    report = {
        "schema_version": "bareflux.robustness_stress.v1",
        "out_dir": str(out.resolve()),
        "scenario_count": len(rows),
        "scenarios": rows,
    }
    (out / "robustness_stress_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    pd.DataFrame(rows).to_csv(out / "robustness_stress_summary.csv", index=False)
    print(f"robustness_stress_report={out / 'robustness_stress_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
