from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


def _import_astropy():
    try:
        from astropy.io import fits  # type: ignore
        from astropy.time import Time  # type: ignore
        return fits, Time
    except Exception as e:
        raise RuntimeError(
            "Dépendance manquante: astropy.\n"
            "Ce module est optionnel et ne fait pas partie du core.\n"
            "Installe astropy uniquement si tu actives le pré-traitement FITS."
        ) from e


def _find_first_ndarray(hdul) -> Tuple[np.ndarray, Dict[str, Any]]:
    for hdu in hdul:
        data = getattr(hdu, "data", None)
        if data is None:
            continue
        try:
            arr = np.asarray(data)
        except Exception:
            continue
        if arr.size == 0:
            continue
        if arr.dtype.fields is not None:
            # table. Pas un "image array"
            continue
        if arr.ndim >= 2:
            hdr = dict(getattr(hdu, "header", {}) or {})
            return arr, hdr
    # fallback: primary hdu si possible
    hdu0 = hdul[0]
    arr = np.asarray(getattr(hdu0, "data", np.array([])))
    hdr = dict(getattr(hdu0, "header", {}) or {})
    return arr, hdr


def _safe_time_from_header(header: Dict[str, Any]) -> Any:
    # On évite de surinterpréter. On extrait un timestamp brut quand dispo.
    for key in ("MJD-OBS", "JD", "DATE-OBS", "DATE"):
        if key in header:
            return header.get(key)
    return None


def extract_basic_features(image: np.ndarray) -> Dict[str, float]:
    img = np.asarray(image, dtype=float)
    img = np.nan_to_num(img, nan=0.0, posinf=0.0, neginf=0.0)

    total = float(np.sum(img))
    if total == 0.0:
        return {"flux": 0.0, "centroid_x": float("nan"), "centroid_y": float("nan"), "fwhm": float("nan")}

    yy, xx = np.indices(img.shape)
    cx = float(np.sum(xx * img) / total)
    cy = float(np.sum(yy * img) / total)

    varx = float(np.sum(((xx - cx) ** 2) * img) / total)
    vary = float(np.sum(((yy - cy) ** 2) * img) / total)
    sigma = float(np.sqrt(max((varx + vary) / 2.0, 0.0)))
    fwhm = 2.355 * sigma
    return {"flux": total, "centroid_x": cx, "centroid_y": cy, "fwhm": fwhm}


def extract_features_from_fits_files(files: Iterable[Path]) -> pd.DataFrame:
    fits, _Time = _import_astropy()

    rows: List[Dict[str, Any]] = []
    for idx, fp in enumerate(files):
        with fits.open(fp) as hdul:
            img, header = _find_first_ndarray(hdul)
        feats = extract_basic_features(img) if img.size else {"flux": 0.0, "centroid_x": float("nan"), "centroid_y": float("nan"), "fwhm": float("nan")}
        t = _safe_time_from_header(header)
        rows.append({"t": t if t is not None else idx, "file": str(fp), **feats})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="Pré-traitement FITS optionnel: extraction descriptive vers CSV.")
    ap.add_argument("--input", type=str, required=True, help="Fichier FITS ou glob, ex data/*.fits")
    ap.add_argument("--out-csv", type=str, required=True, help="Chemin CSV de sortie")
    args = ap.parse_args()

    pattern = args.input
    paths = sorted([Path(p) for p in Path().glob(pattern)]) if any(ch in pattern for ch in "*?[]") else [Path(pattern)]
    paths = [p for p in paths if p.exists()]

    if not paths:
        raise FileNotFoundError(f"Aucun FITS trouvé pour input={args.input}")

    df = extract_features_from_fits_files(paths)
    out = Path(args.out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"fits_features_csv={out.resolve()}")


if __name__ == "__main__":
    main()
