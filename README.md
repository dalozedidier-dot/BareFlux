# BareFlux

BareFlux est l'orchestrateur du bloc 4. Il lance RiftLens, NullTrace et VoidMark sur des jeux de donnees reproductibles, puis produit un manifeste d'audit qui permet de verifier les entrees, les modules, les sorties et les hashes.

## Identite du depot

Le depot est maintenant coherent : le package Python installe est `BareFlux`, le CLI est `bareflux`, et le code Python interne vit sous `src/bareflux/`.

Il n'y a plus de package `apexobserver` concurrent.

## Installation locale

```bash
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## CLI minimal

```bash
bareflux --help
bareflux run --input examples/minimal_timeseries.csv --output _bareflux_observer_out
python -m bareflux.orchestration strict-check --out-dir _bareflux_out
```

## Orchestration bloc 4

BareFlux attend trois modules :

```text
modules/RiftLens/src
modules/NullTrace/src
modules/VoidMark/src
```

Exemple :

```bash
./run_modules.sh --modules-dir modules --out _bareflux_out --strict
```

En absence de CSV fournis, BareFlux genere automatiquement des datasets synthetiques dans `_ci_out/datasets/`.

## Artefacts principaux

```text
_bareflux_out/riftlens/graph_report.json
_bareflux_out/nulltrace_prev/shadows/*/manifest.json
_bareflux_out/nulltrace_curr/shadows/*/manifest.json
_bareflux_out/nulltrace_curr/shadows/*/shadow_diff.json
_bareflux_out/vault/**
_bareflux_out/bareflux_manifest.json
```

Le fichier `bareflux_manifest.json` contient :

```text
schema_version
status
modules et commits Git si disponibles
datasets avec hashes sha256
sorties produites avec hashes sha256
strict_errors
```

## Workflows conserves

```text
.github/workflows/ci.yml
.github/workflows/orchestrate.yml
.github/workflows/collect-stable.yml
.github/workflows/mass-collect.yml
.github/workflows/apply-repo-settings.yml
.github/workflows/run-all.yml
```

`run-all.yml` est conserve comme workflow de compatibilite pour les anciens appels.
Le workflow redondant `bareflux-improvements.yml` a ete supprime.

## Stabilite et robustesse

Generation des datasets de base :

```bash
python tools/generate_synth_datasets.py --out-dir _ci_out/datasets --n 200 --seed 42
```

Stress tests reproductibles :

```bash
python tools/robustness_stress_tests.py --out-dir _ci_out/robustness --n 240 --seed 7000
```

Synthese mass-collect :

```bash
python tools/mass_collect_overview.py \
  --mass-dir _ci_out/mass \
  --out-json _ci_out/mass/mass_collect_overview.json \
  --out-csv _ci_out/mass/mass_collect_summary.csv
```

## Verification locale

```bash
python -m compileall src tests tools examples
black --check src tests tools examples
pytest -q
mypy src/bareflux
```
