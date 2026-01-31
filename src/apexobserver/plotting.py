from __future__ import annotations
from pathlib import Path
from typing import List
import numpy as np
import matplotlib.pyplot as plt

def _downsample(x: np.ndarray, max_points: int) -> np.ndarray:
    n = len(x)
    if n <= max_points:
        return x
    idx = np.linspace(0, n - 1, num=max_points).astype(int)
    return x[idx]

def plot_overview(series: np.ndarray, ruptures: List[int], out_path: Path, max_points: int = 5000) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    y = series.astype(float)
    y_ds = _downsample(y, max_points=max_points)
    if len(y) > len(y_ds) and ruptures:
        scale = (len(y_ds) - 1) / max(1, (len(y) - 1))
        r_ds = sorted(set(int(round(i * scale)) for i in ruptures if i >= 0))
    else:
        r_ds = ruptures
    plt.figure()
    plt.plot(y_ds)
    for r in r_ds:
        if 0 <= r < len(y_ds):
            plt.axvline(r, linestyle="--")
    plt.title("ApexObserver - Overview")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
