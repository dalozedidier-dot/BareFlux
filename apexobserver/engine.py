from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from .hashing import write_hashes_file


@dataclass
class SeriesConfig:
    name: str
    value_col: str
    time_col: Optional[str] = None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _make_run_id(ts: datetime) -> str:
    # Example: 20260130T120102Z_ab12cd
    suffix = np.random.default_rng().integers(0, 16**6, dtype=np.int64)
    return f"{ts.strftime('%Y%m%dT%H%M%SZ')}_{suffix:06x}"


def _guess_value_col(df: pd.DataFrame) -> str:
    # Prefer common names
    for c in ["value", "y", "metric", "v"]:
        if c in df.columns:
            return c
    # Else pick first numeric column
    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric:
        raise ValueError("No numeric column found. Specify value_col in config.")
    return numeric[0]


def _guess_time_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["timestamp", "time", "date", "datetime", "t"]:
        if c in df.columns:
            return c
    return None


def _load_series(df: pd.DataFrame, scfg: SeriesConfig) -> Tuple[pd.Series, Optional[pd.Series], List[str]]:
    warnings: List[str] = []
    if scfg.value_col not in df.columns:
        raise ValueError(f"value_col '{scfg.value_col}' not found in input columns: {list(df.columns)}")

    y = pd.to_numeric(df[scfg.value_col], errors="coerce")
    t = None
    if scfg.time_col:
        if scfg.time_col not in df.columns:
            warnings.append(f"time_col '{scfg.time_col}' not found; using row index as time")
        else:
            t = df[scfg.time_col].astype(str)
    return y, t, warnings


def _linreg_slope(y: np.ndarray) -> float:
    # Slope of y against index 0..n-1 using least squares; returns nan if insufficient data
    n = len(y)
    if n < 2:
        return float("nan")
    x = np.arange(n, dtype=float)
    mask = np.isfinite(y)
    if mask.sum() < 2:
        return float("nan")
    x = x[mask]
    yy = y[mask]
    x_mean = x.mean()
    y_mean = yy.mean()
    denom = ((x - x_mean) ** 2).sum()
    if denom == 0:
        return float("nan")
    return float(((x - x_mean) * (yy - y_mean)).sum() / denom)


def _describe(y: pd.Series) -> Dict[str, Any]:
    arr = y.to_numpy(dtype=float)
    finite = arr[np.isfinite(arr)]
    stats: Dict[str, Any] = {
        "count": int(len(arr)),
        "finite_count": int(np.isfinite(arr).sum()),
        "missing_count": int(np.isnan(arr).sum()),
    }
    if len(finite) == 0:
        stats.update({k: None for k in ["mean", "std", "min", "max", "median", "p05", "p95", "trend_slope"]})
        return stats

    stats.update(
        {
            "mean": float(np.mean(finite)),
            "std": float(np.std(finite, ddof=1)) if len(finite) > 1 else 0.0,
            "min": float(np.min(finite)),
            "max": float(np.max(finite)),
            "median": float(np.median(finite)),
            "p05": float(np.quantile(finite, 0.05)),
            "p95": float(np.quantile(finite, 0.95)),
            "trend_slope": _linreg_slope(arr),
        }
    )
    return stats


def _rupture_marks(y: pd.Series, t: Optional[pd.Series], z_threshold: float) -> pd.DataFrame:
    # Minimal detector: z-score of first differences
    dy = y.diff()
    arr = dy.to_numpy(dtype=float)
    finite = arr[np.isfinite(arr)]
    if len(finite) < 2:
        return pd.DataFrame(columns=["idx", "time", "value", "diff", "z", "kind"])
    mu = float(np.mean(finite))
    sd = float(np.std(finite, ddof=1)) if len(finite) > 1 else 0.0
    if sd == 0.0:
        return pd.DataFrame(columns=["idx", "time", "value", "diff", "z", "kind"])

    z = (arr - mu) / sd
    idxs = np.where(np.isfinite(z) & (np.abs(z) >= z_threshold))[0]
    rows = []
    for i in idxs:
        rows.append(
            {
                "idx": int(i),
                "time": (t.iloc[i] if t is not None and i < len(t) else ""),
                "value": (float(y.iloc[i]) if i < len(y) and pd.notna(y.iloc[i]) else float("nan")),
                "diff": (float(dy.iloc[i]) if i < len(dy) and pd.notna(dy.iloc[i]) else float("nan")),
                "z": float(z[i]),
                "kind": "diff_spike",
            }
        )
    return pd.DataFrame(rows, columns=["idx", "time", "value", "diff", "z", "kind"])


def _series_features(stats: Dict[str, Any], ruptures: pd.DataFrame) -> pd.DataFrame:
    # Key/value table to keep it dead simple.
    feats = [
        ("count", stats["count"]),
        ("finite_count", stats["finite_count"]),
        ("missing_count", stats["missing_count"]),
        ("mean", stats["mean"]),
        ("std", stats["std"]),
        ("min", stats["min"]),
        ("max", stats["max"]),
        ("median", stats["median"]),
        ("p05", stats["p05"]),
        ("p95", stats["p95"]),
        ("trend_slope", stats["trend_slope"]),
        ("rupture_count", int(len(ruptures))),
    ]
    return pd.DataFrame(feats, columns=["feature", "value"])


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _zip_dir(zip_path: Path, root_dir: Path, rel_paths: List[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in rel_paths:
            abs_path = root_dir / rel
            zf.write(abs_path, rel.as_posix())


def _series_config_from_config(config: Dict[str, Any], input_csv: Path, df: pd.DataFrame) -> Tuple[SeriesConfig, Dict[str, Any]]:
    # Minimal supported config:
    # {
    #   "series_name": "minimal",
    #   "value_col": "value",
    #   "time_col": "timestamp",
    #   "rupture": {"z_threshold": 3.0}
    # }
    name = str(config.get("series_name") or input_csv.stem)
    value_col = str(config.get("value_col") or _guess_value_col(df))
    time_col = config.get("time_col")
    if time_col is not None:
        time_col = str(time_col)
    else:
        time_col = _guess_time_col(df)
    rupture = config.get("rupture") or {}
    z_threshold = float(rupture.get("z_threshold", 3.0))
    return SeriesConfig(name=name, value_col=value_col, time_col=time_col), {"z_threshold": z_threshold}


def run_observer(input_csv: Path, output_root: Path, config: Dict[str, Any], cli_argv=None) -> Path:
    if not input_csv.exists():
        raise SystemExit(f"Input not found: {input_csv}")

    output_root.mkdir(parents=True, exist_ok=True)
    ts = _now_utc()
    run_id = _make_run_id(ts)
    run_dir = output_root / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)

    # Snapshot inputs for auditability
    inputs_dir = run_dir / "inputs"
    inputs_dir.mkdir()
    shutil.copy2(input_csv, inputs_dir / input_csv.name)

    config_used_path = run_dir / "config_used.json"
    _write_json(config_used_path, config)

    df = pd.read_csv(input_csv)
    series_cfg, rupture_cfg = _series_config_from_config(config, input_csv, df)

    series_dir = run_dir / "series" / series_cfg.name
    series_dir.mkdir(parents=True)

    errors: List[str] = []
    warnings: List[str] = []

    try:
        y, t, w = _load_series(df, series_cfg)
        warnings.extend(w)
        stats = _describe(y)
        ruptures = _rupture_marks(y, t, z_threshold=rupture_cfg["z_threshold"])
        features = _series_features(stats, ruptures)

        report = {
            "tool": "ApexObserver",
            "version": "0.1.0",
            "series_name": series_cfg.name,
            "input": {"csv": str(input_csv), "value_col": series_cfg.value_col, "time_col": series_cfg.time_col},
            "rupture": {"method": "zscore_first_diff", "z_threshold": rupture_cfg["z_threshold"], "count": int(len(ruptures))},
            "stats": stats,
            "generated_at_utc": ts.isoformat(),
        }

        _write_json(series_dir / "report.json", report)
        features.to_csv(series_dir / "features.csv", index=False)
        ruptures.to_csv(series_dir / "rupture_marks.csv", index=False)

    except Exception as e:
        errors.append(str(e))
        # Still write placeholder files so the run folder is structurally consistent.
        _write_json(series_dir / "report.json", {"tool": "ApexObserver", "version": "0.1.0", "series_name": series_cfg.name, "error": str(e)})
        pd.DataFrame([["error", str(e)]], columns=["feature", "value"]).to_csv(series_dir / "features.csv", index=False)
        pd.DataFrame(columns=["idx", "time", "value", "diff", "z", "kind"]).to_csv(series_dir / "rupture_marks.csv", index=False)

    _write_json(series_dir / "errors.json", {"errors": errors, "warnings": warnings})

    # Run manifest (no self-referential hashes; hashes live in hashes.sha256)
    manifest = {
        "tool": "ApexObserver",
        "version": "0.1.0",
        "run_id": run_id,
        "created_at_utc": ts.isoformat(),
        "command": " ".join(["apexobserver"] + (cli_argv or [])) if cli_argv is not None else "apexobserver run",
        "inputs": [{"path": f"inputs/{input_csv.name}", "kind": "csv"}],
        "config": {"path": "config_used.json"},
        "series": [
            {
                "name": series_cfg.name,
                "path": f"series/{series_cfg.name}",
                "artifacts": [
                    "report.json",
                    "features.csv",
                    "rupture_marks.csv",
                    "errors.json",
                ],
            }
        ],
    }
    run_manifest_path = run_dir / "run_manifest.json"
    _write_json(run_manifest_path, manifest)

    # Build bundle.zip with auditable contents (excluding hashes.sha256 itself)
    bundle_rel_paths = [
        Path("run_manifest.json"),
        Path("config_used.json"),
        Path("inputs") / input_csv.name,
        Path("series") / series_cfg.name / "report.json",
        Path("series") / series_cfg.name / "features.csv",
        Path("series") / series_cfg.name / "rupture_marks.csv",
        Path("series") / series_cfg.name / "errors.json",
    ]
    bundle_zip_path = run_dir / "bundle.zip"
    _zip_dir(bundle_zip_path, run_dir, bundle_rel_paths)

    # hashes.sha256 includes sha256 for everything above + bundle.zip (but not hashes.sha256)
    hash_rel_paths = bundle_rel_paths + [Path("bundle.zip")]
    write_hashes_file(run_dir, hash_rel_paths, out_name="hashes.sha256")

    return run_dir
