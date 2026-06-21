# BareFlux v0.2.0 patch notes

## Nettoyage d'identite

- Package Python renomme en `BareFlux` dans `pyproject.toml`.
- CLI officiel ajoute : `bareflux`.
- Suppression des packages concurrents `apexobserver/` et `src/apexobserver/`.
- Code interne consolide sous `src/bareflux/`.
- Config exemple renomme en `examples/bareflux.json`.
- Config par defaut renomme en `configs/bareflux_default.json`.

## Orchestration

- `run_modules.sh` reecrit.
- Ajout du mode strict contractuel.
- Ajout de `bareflux_manifest.json` en sortie.
- `--parallel` est accepte pour compatibilite, mais reste sequentiel.
- Ajout de `--corr-threshold`.

## Workflows

- Workflows conserves : `ci.yml`, `orchestrate.yml`, `collect-stable.yml`, `mass-collect.yml`, `apply-repo-settings.yml`.
- Workflows supprimes : `run-all.yml`, `bareflux-improvements.yml`.
- Unification sur `.github/constraints.txt`.
- Installation de VoidMark ajoutee dans les workflows d'orchestration, de stabilite et de collecte massive.

## Artefacts nouveaux

- `_bareflux_out/bareflux_manifest.json`
- `_ci_out/mass/mass_collect_overview.json`
- `_ci_out/mass/mass_collect_summary.csv`
- `_ci_out/robustness/robustness_stress_report.json`
- `_ci_out/robustness/robustness_stress_summary.csv`

## Schemas nouveaux

- `schema/bareflux_manifest.schema.json`
- `schema/mass_collect_overview.schema.json`
- `schema/robustness_stress.schema.json`

## Tests ajoutes

- Test strict de `run_modules.sh` avec faux modules RiftLens, NullTrace et VoidMark.
- Test de generation du manifeste strict.
- Test de generation des stress datasets.

## Verification locale effectuee

```bash
python -m compileall src tests tools examples
black --check src tests tools examples
pytest -q
mypy src/bareflux
```

Resultat observe :

```text
black: OK
pytest: 6 passed
mypy: Success, no issues found
```
