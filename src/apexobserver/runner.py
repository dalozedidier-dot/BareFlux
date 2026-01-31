from __future__ import annotations
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .engine import analyze_series
from .plotting import plot_overview
from .schema import validate_config, validate_report
from .utils import sha256_file, write_hashes_sha256

def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _safe_read_csv(path: Path) -> Tuple[Optional[pd.DataFrame], List[str], List[str]]:
    warnings: List[str] = []
    errors: List[str] = []
    try:
        df = pd.read_csv(path)
        if df.empty:
            warnings.append("csv_empty")
        return df, warnings, errors
    except Exception as e:
        errors.append(f"read_csv_failed:{type(e).__name__}:{e}")
        return None, warnings, errors

def _detect_numeric_columns(df: pd.DataFrame) -> List[str]:
    cols = []
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(str(c))
    return cols

def run_one_csv(input_csv: Path, output_dir: Path, cfg: Dict[str, Any], report_schema_path: Path) -> Dict[str, Any]:
    t0 = time.time()
    run_id = str(uuid.uuid4())
    out = output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "meta").mkdir(exist_ok=True)
    (out / "plots").mkdir(exist_ok=True)

    warnings: List[str] = []
    errors: List[str] = []

    df, w, e = _safe_read_csv(input_csv)
    warnings.extend(w)
    errors.extend(e)

    status = "ok"
    observations: Dict[str, Any] = {}

    series_clean_path = out / "series_clean.csv"
    features_path = out / "features.csv"
    ruptures_path = out / "rupture_marks.csv"

    if df is None:
        status = "invalid_input"
    else:
        ts_col = cfg.get("timestamp_column")
        series_cols = cfg.get("series_columns") or _detect_numeric_columns(df)
        series_cols = [c for c in series_cols if c in df.columns]

        if not series_cols:
            status = "invalid_input"
            errors.append("no_numeric_series_columns")
        else:
            np.random.seed(int(cfg.get("seed", 0)))

            out_df = pd.DataFrame()
            if ts_col and ts_col in df.columns:
                out_df[ts_col] = df[ts_col]
            for c in series_cols:
                coerced = pd.to_numeric(df[c], errors="coerce")
                newly_nan = int(coerced.isna().sum() - pd.Series(df[c]).isna().sum())
                if newly_nan > 0:
                    warnings.append(f"coerce_to_numeric:{c}:{newly_nan}")
                out_df[c] = coerced

            out_df.to_csv(series_clean_path, index=False)

            feats_rows = []
            rup_rows = []
            for c in series_cols:
                x = out_df[c].to_numpy(dtype=float)
                obs = analyze_series(x, cfg)
                observations[c] = obs

                row = {"column": c}
                row.update({f"stat_{k}": v for k, v in obs["stats"].items()})
                row.update({f"missing_{k}": v for k, v in obs["missing"].items()})
                row.update({f"outlier_{k}": v for k, v in obs["outliers"].items()})
                row["rupture_count"] = len(obs["ruptures"]["indices"])
                feats_rows.append(row)

                for idx, score in zip(obs["ruptures"]["indices"], obs["ruptures"]["scores"]):
                    rup_rows.append({"column": c, "index": int(idx), "score": float(score)})

                try:
                    plot_overview(x, list(obs["ruptures"]["indices"]), out / "plots" / f"overview_{c}.png", int(cfg.get("max_points_plot", 5000)))
                except Exception as pe:
                    warnings.append(f"plot_failed:{c}:{type(pe).__name__}:{pe}")

            pd.DataFrame(feats_rows).to_csv(features_path, index=False)
            pd.DataFrame(rup_rows).to_csv(ruptures_path, index=False)

    env = {"python": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}", "platform": os.name}
    (out / "meta" / "env.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    (out / "meta" / "timings.json").write_text(json.dumps({"runtime_seconds": float(time.time() - t0)}, indent=2), encoding="utf-8")
    (out / "meta" / "warnings.json").write_text(json.dumps(warnings, indent=2), encoding="utf-8")
    (out / "meta" / "errors.json").write_text(json.dumps(errors, indent=2), encoding="utf-8")

    rep: Dict[str, Any] = {
        "schema_version": "apexobserver.report.v1",
        "run_id": run_id,
        "utc_start": utc_now(),
        "utc_end": utc_now(),
        "status": status,
        "input": {"source": input_csv.as_posix(), "sha256": sha256_file(input_csv) if input_csv.exists() else ""},
        "observations": observations,
        "warnings": warnings,
        "errors": errors,
    }

    try:
        validate_report(rep, report_schema_path)
    except Exception as ve:
        rep["status"] = "partial" if rep["status"] == "ok" else rep["status"]
        rep.setdefault("warnings", []).append(f"report_schema_validation_failed:{type(ve).__name__}:{ve}")

    (out / "report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "schema_version": "apexobserver.manifest.v1",
        "run_id": run_id,
        "utc_created": utc_now(),
        "config": cfg,
        "paths": {"report": "report.json", "series_clean": "series_clean.csv", "features": "features.csv", "rupture_marks": "rupture_marks.csv"},
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    write_hashes_sha256(out)
    return rep

def run_batch(inputs: List[Path], output_dir: Path, cfg: Dict[str, Any], report_schema_path: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = output_dir / "runs"
    runs_dir.mkdir(exist_ok=True)

    batch_id = uuid.uuid4().hex
    batch = {"schema_version": "apexobserver.batch.v1", "batch_id": batch_id, "utc_start": utc_now(), "inputs": [p.as_posix() for p in inputs], "runs": []}

    for p in inputs:
        run_out = runs_dir / f"{p.stem}__{uuid.uuid4().hex[:8]}"
        rep = run_one_csv(p, run_out, cfg, report_schema_path)
        batch["runs"].append({"input": p.as_posix(), "status": rep.get("status", ""), "run_dir": run_out.relative_to(output_dir).as_posix()})

    batch["utc_end"] = utc_now()
    (output_dir / "batch_manifest.json").write_text(json.dumps(batch, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_dir / "batch_manifest.json"
