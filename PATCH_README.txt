Patch générique — Ruff UP047 (PEP 695) pour `perf_timer`
Date: 2026-02-03

Symptôme:
  common/utils.py:...: UP047 Generic function `perf_timer` should use type parameters

Correctif:
  - Conversion de `perf_timer` vers la syntaxe PEP 695 (Python 3.12+):
      def perf_timer[**P, R](func: Callable[P, R]) -> Callable[P, R]:

Installation:
  1) Dézip à la racine du repo qui contient `common/utils.py`
  2) Exécute:
       python tools/fix_up047_perf_timer.py --file common/utils.py
  3) Commit + push
  4) Relance le workflow lint

Notes:
  - Le script tente de retirer les lignes adjacentes:
      P = ParamSpec("P") / R = TypeVar("R")
    uniquement si elles sont juste au-dessus de perf_timer.
  - Il retire aussi ParamSpec/TypeVar des imports `typing` si devenus inutiles.
