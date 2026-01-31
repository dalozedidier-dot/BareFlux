# BareFlux orchestration autonome

## Objectif
BareFlux orchestre NullTrace, RiftLens, VoidMark sans couplage fort.
Il peut fonctionner si les modules sont des dossiers adjacents ou clonés dans `./modules/`.

## Local
Si tu as les repos côte à côte :
NullTrace
RiftLens
VoidMark
BareFlux

Depuis BareFlux :
```bash
chmod +x run_modules.sh
./run_modules.sh --out _bareflux_out
```

Mode strict :
```bash
./run_modules.sh --out _bareflux_out --strict
```

Parallélisation (NullTrace + RiftLens en parallèle) :
```bash
./run_modules.sh --parallel
```

## CI
Le workflow `.github/workflows/orchestrate.yml` :
clone les 3 repos dans `modules/`
installe les dépendances
lance `run_modules.sh`
uploade les outputs comme artifact
