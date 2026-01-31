from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Callable, Iterable, List, Optional, Sequence, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def parallel_map(func: Callable[[T], R], items: Sequence[T], max_workers: Optional[int] = None) -> List[R]:
    """Parallélisme massif minimal (stdlib), sans dépendances lourdes."""
    results: List[R] = []
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(func, it) for it in items]
        for fut in as_completed(futs):
            results.append(fut.result())
    return results
