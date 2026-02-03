#!/usr/bin/env python3
"""
Profils de bruit structurés (VoidMark) :
- gaussian
- subset_shift
- correlated_blocks
"""
from __future__ import annotations

import random


def gaussian(n, mu=0.0, sigma=1.0, seed=0):
    rnd = random.Random(seed)
    return [rnd.gauss(mu, sigma) for _ in range(n)]


def subset_shift(n, frac=0.1, shift=0.5, seed=0):
    rnd = random.Random(seed)
    x = [rnd.gauss(0.0, 1.0) for _ in range(n)]
    k = max(1, int(n * frac))
    idx = rnd.sample(range(n), k)
    for i in idx:
        x[i] += shift
    return x


def correlated_blocks(n, block=10, rho=0.8, seed=0):
    rnd = random.Random(seed)
    x = []
    prev = 0.0
    for i in range(n):
        if i % block == 0:
            prev = rnd.gauss(0.0, 1.0)
        val = rho * prev + (1 - rho) * rnd.gauss(0.0, 1.0)
        x.append(val)
        prev = val
    return x
