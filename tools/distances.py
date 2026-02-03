#!/usr/bin/env python3
"""
Distances de distributions (sans dépendances externes obligatoires).
- Energy distance (exact)
- Wasserstein-1 distance (approx, 1D)

Notes:
- Utile pour détecter des shifts subtils que mean/std ratent.
"""
from __future__ import annotations


def wasserstein_1d(x, y):
    xs = sorted(float(v) for v in x)
    ys = sorted(float(v) for v in y)
    n = len(xs)
    m = len(ys)
    if n == 0 or m == 0:
        return None

    i = j = 0
    cdfx = cdfy = 0.0
    last = None
    area = 0.0

    while i < n or j < m:
        if j >= m or (i < n and xs[i] <= ys[j]):
            nxt = xs[i]
        else:
            nxt = ys[j]

        if last is not None:
            area += abs(cdfx - cdfy) * (nxt - last)

        while i < n and xs[i] == nxt:
            i += 1
        while j < m and ys[j] == nxt:
            j += 1

        cdfx = i / n
        cdfy = j / m
        last = nxt

    return float(area)


def energy_distance(x, y):
    x = [float(v) for v in x]
    y = [float(v) for v in y]
    n = len(x)
    m = len(y)
    if n == 0 or m == 0:
        return None

    def avg_abs(a, b):
        s = 0.0
        for i in a:
            for j in b:
                s += abs(i - j)
        return s / (len(a) * len(b))

    exy = avg_abs(x, y)
    exx = avg_abs(x, x)
    eyy = avg_abs(y, y)
    return float(2.0 * exy - exx - eyy)
