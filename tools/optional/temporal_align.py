from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np


def phase_fold(times: Sequence[float], period: float, t0: float = 0.0) -> np.ndarray:
    """Phasage brut, descriptif, sans modèle."""
    times_arr = np.asarray(times, dtype=float)
    if period <= 0:
        raise ValueError("period doit être > 0")
    return ((times_arr - t0) % period) / period


@dataclass(frozen=True)
class ObserverLocation:
    lon_deg: float
    lat_deg: float
    height_m: float = 0.0


def barycentric_correct_jd(times_jd: Sequence[float], ra_deg: float, dec_deg: float, location: ObserverLocation) -> np.ndarray:
    """Correction barycentrique avec astropy si installé.

    Important: ce module est optionnel. Le core ne dépend pas de cette fonction.
    """
    try:
        from astropy.coordinates import SkyCoord, EarthLocation  # type: ignore
        from astropy.time import Time  # type: ignore
        import astropy.units as u  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Dépendance manquante: astropy (coordinates/time/units).\n"
            "Ce module est optionnel et ne fait pas partie du core."
        ) from e

    t = Time(np.asarray(times_jd, dtype=float), format="jd", scale="utc", location=EarthLocation(lon=location.lon_deg * u.deg, lat=location.lat_deg * u.deg, height=location.height_m * u.m))
    target = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")

    ltt = t.light_travel_time(target, kind="barycentric")
    t_bary = t.tdb + ltt
    return np.asarray(t_bary.jd, dtype=float)
