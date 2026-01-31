from __future__ import annotations

from typing import Optional, Sequence

import numpy as np


def lomb_scargle_power(times: Sequence[float], values: Sequence[float], freqs: Sequence[float]) -> np.ndarray:
    """Lomb-Scargle via astropy si dispo.

    C'est du post-traitement optionnel. A utiliser explicitement, hors core.
    """
    try:
        from astropy.timeseries import LombScargle  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Dépendance manquante: astropy.timeseries.\n"
            "Installe astropy uniquement si tu actives ce module optionnel."
        ) from e

    t = np.asarray(times, dtype=float)
    y = np.asarray(values, dtype=float)
    f = np.asarray(freqs, dtype=float)
    ls = LombScargle(t, y)
    return np.asarray(ls.power(f), dtype=float)


def transit_model_batman(times: Sequence[float], period: float, t0: float, rp: float, a: float, inc_deg: float = 90.0) -> np.ndarray:
    """Modèle transit via batman si dispo.

    Attention: c'est un modèle physique, donc interprétatif par nature.
    On le garde optionnel, en post-traitement.
    """
    try:
        import batman  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Dépendance manquante: batman-package.\n"
            "Installe-la uniquement si tu actives le module de modélisation."
        ) from e

    params = batman.TransitParams()
    params.t0 = float(t0)
    params.per = float(period)
    params.rp = float(rp)
    params.a = float(a)
    params.inc = float(inc_deg)
    params.ecc = 0.0
    params.w = 90.0
    params.limb_dark = "quadratic"
    params.u = [0.1, 0.3]

    t = np.asarray(times, dtype=float)
    m = batman.TransitModel(params, t)
    return np.asarray(m.light_curve(params), dtype=float)
