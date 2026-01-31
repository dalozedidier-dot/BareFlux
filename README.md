# BareFlux

Orchestrateur minimal pour exécuter RiftLens, NullTrace, VoidMark dans un même workspace.

## Pré requis
**Les 4 dossiers doivent être côte à côte** dans un même répertoire parent (même niveau) :

```
GitHub/
├─ BareFlux/
├─ RiftLens/
├─ NullTrace/
└─ VoidMark/
```

`run_modules.sh` suppose cet agencement (références par chemins relatifs).


## Exécution rapide
chmod +x run_modules.sh
./run_modules.sh

## Objectif
Fournir une orchestration loose, reproductible et vérifiable, sans couplage fort entre modules.
