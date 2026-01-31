# BareFlux

Orchestrateur minimal pour exécuter RiftLens, NullTrace, VoidMark dans un même workspace.

## Prérequis

**Les 4 dossiers doivent être côte à côte dans un même répertoire parent** :

- RiftLens
- NullTrace
- VoidMark
- BareFlux

Schéma attendu :

```
workspace/
  BareFlux/
  RiftLens/
  NullTrace/
  VoidMark/
```

## Exécution rapide

```
chmod +x run_modules.sh
./run_modules.sh
```

## Où récupérer les sorties

- RiftLens : `RiftLens/outputs/` (si `--output-dir outputs` est utilisé)
- NullTrace : `NullTrace/outputs/`
- VoidMark : dans le répertoire `--vault-dir` (ex: `VoidMark/vault_test/`)

## Objectif

Fournir une orchestration loose, reproductible et vérifiable, sans couplage fort entre modules.
