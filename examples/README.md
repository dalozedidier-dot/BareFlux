# Exemples prêts à l’emploi — stats BareFlux / RiftLens / VoidMark
Date: 2026-02-03

Objectif : extraire, calculer et présenter des statistiques impactantes à partir des artefacts (CSV/JSON).

## Dépendances
- pandas (pour les CSV)
- Python stdlib (json)

Installation rapide :
```bash
python -m pip install -U pandas
```

## Scripts
- extract_and_print.py : imprime un résumé (shadow diff / RiftLens / VoidMark / score)
- make_report_md.py : génère un mini rapport Markdown (README/article)

Chemins :
- par défaut: dossier courant
- sinon: --path _bareflux_out
