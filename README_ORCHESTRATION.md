# BareFlux orchestration

## Objectif

BareFlux orchestre RiftLens, NullTrace et VoidMark sans couplage fort. Le contrat principal est simple : chaque module produit ses artefacts, puis BareFlux ecrit un `bareflux_manifest.json` qui trace les entrees, les sorties, les hashes et les erreurs de controle strict.

## Structure attendue

```text
BareFlux/
modules/
  RiftLens/src/
  NullTrace/src/
  VoidMark/src/
```

Les modules peuvent aussi etre places comme dossiers adjacents au depot BareFlux.

## Execution locale

```bash
./run_modules.sh --modules-dir modules --out _bareflux_out
```

Mode strict :

```bash
./run_modules.sh --modules-dir modules --out _bareflux_out --strict
```

Option acceptee pour compatibilite :

```bash
./run_modules.sh --parallel
```

Cette option est reconnue mais l'execution reste sequentielle tant que les contrats inter-modules ne sont pas parallelisables sans risque.

## Contrat strict

Le mode strict exige :

```text
riftlens/graph_report.json
nulltrace_prev/shadows/*/manifest.json
nulltrace_curr/shadows/*/manifest.json
nulltrace_curr/shadows/*/shadow_diff.json
vault/**/*
bareflux_manifest.json
```

Si un artefact manque, le manifeste est ecrit avec `status = FAIL` et la liste `strict_errors` explique le blocage.

## CI

`orchestrate.yml` clone les trois modules, installe leurs dependances avec `.github/constraints.txt`, lance `run_modules.sh --strict`, puis publie les artefacts.

`run-all.yml` reste present comme workflow de compatibilite. Le workflow canonique pour l'orchestration stricte est `orchestrate.yml`.

`collect-stable.yml` mesure la stabilite sur plusieurs seuils et genere aussi les jeux de stress.

`mass-collect.yml` repete les runs, puis produit :

```text
_ci_out/mass/mass_collect_overview.json
_ci_out/mass/mass_collect_summary.csv
```
