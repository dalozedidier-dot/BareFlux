from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
import numpy as np
import pandas as pd

@dataclass
class RuptureResult:
    indices: List[int]
    scores: List[float]

def rolling_mean_delta_topk(x: np.ndarray, window: int, topk: int) -> RuptureResult:
    window = max(2, int(window))
    n = len(x)
    if n < window * 2:
        return RuptureResult(indices=[], scores=[])
    s = pd.Series(x)
    m = s.rolling(window=window, min_periods=window).mean().to_numpy()
    dm = np.abs(np.diff(np.nan_to_num(m, nan=0.0)))
    if dm.size == 0:
        return RuptureResult(indices=[], scores=[])
    k = min(int(topk), dm.size)
    idx = np.argpartition(-dm, kth=k-1)[:k]
    idx = idx[np.argsort(-dm[idx])]
    indices = (idx + 1).astype(int).tolist()
    scores = dm[idx].astype(float).tolist()
    return RuptureResult(indices=indices, scores=scores)

def rolling_zscore_outliers(x: np.ndarray, window: int, z_th: float) -> Dict[str, float]:
    window = max(5, int(window))
    s = pd.Series(x)
    mu = s.rolling(window=window, min_periods=window).mean()
    sig = s.rolling(window=window, min_periods=window).std(ddof=0).replace(0, np.nan)
    z = (s - mu) / sig
    mask = np.abs(z.to_numpy()) >= float(z_th)
    count = int(np.nansum(mask))
    total = int(np.sum(~np.isnan(s.to_numpy())))
    return {"outlier_count": count, "observed_count": total, "outlier_density": float(count/total) if total else 0.0}

def fft_peaks(x: np.ndarray, topk: int, min_period: int) -> Dict[str, List[Dict[str, float]]]:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 8:
        return {"peaks": []}
    x0 = x - np.mean(x)
    spec = np.fft.rfft(x0)
    amp = np.abs(spec)
    amp[0] = 0.0
    freqs = np.fft.rfftfreq(n, d=1.0)
    k = min(int(topk), len(amp))
    idx = np.argpartition(-amp, kth=k-1)[:k]
    idx = idx[np.argsort(-amp[idx])]
    peaks = []
    for i in idx:
        f = float(freqs[i])
        if f <= 0:
            continue
        period = float(1.0 / f)
        if period < float(min_period):
            continue
        peaks.append({"frequency": f, "period": period, "amplitude": float(amp[i])})
    return {"peaks": peaks}

def basic_stats(x: np.ndarray) -> Dict[str, float]:
    x = np.asarray(x, dtype=float)
    n = int(np.sum(~np.isnan(x)))
    if n == 0:
        nan = float("nan")
        return {"count": 0.0, "mean": nan, "std": nan, "min": nan, "max": nan, "p25": nan, "p50": nan, "p75": nan}
    return {
        "count": float(n),
        "mean": float(np.nanmean(x)),
        "std": float(np.nanstd(x)),
        "min": float(np.nanmin(x)),
        "max": float(np.nanmax(x)),
        "p25": float(np.nanpercentile(x, 25)),
        "p50": float(np.nanpercentile(x, 50)),
        "p75": float(np.nanpercentile(x, 75)),
    }

def analyze_series(x: np.ndarray, cfg: Dict) -> Dict:
    obs = {}
    obs["stats"] = basic_stats(x)
    obs["missing"] = {
        "nan_count": int(np.sum(np.isnan(x))),
        "total": int(len(x)),
        "nan_ratio": float(np.sum(np.isnan(x)) / len(x)) if len(x) else 0.0,
    }
    obs["outliers"] = rolling_zscore_outliers(x, cfg["outliers"]["window"], cfg["outliers"]["z_threshold"])
    rr = rolling_mean_delta_topk(x, cfg["rupture"]["window"], cfg["rupture"]["topk"])
    obs["ruptures"] = {"method": str(cfg["rupture"]["method"]), "indices": rr.indices, "scores": rr.scores}
    obs["seasonality"] = fft_peaks(x, cfg["seasonality"]["fft_topk"], cfg["seasonality"]["min_period"])
    return obs
