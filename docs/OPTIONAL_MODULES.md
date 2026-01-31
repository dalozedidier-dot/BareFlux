# Modules optionnels non intrusifs (pré et post traitement)

Ce document décrit une extension possible du bloc 4 sans modifier les invariants du core.

Invariants conservés
1) Observation brute non narrative.
2) Diff neutre, aucune causalité forcée.
3) Marque immuable.
4) Orchestration loose.
5) Activation explicite par l'utilisateur.

Le principe est simple: tout ajout se fait en amont (pré-traitement) ou en aval (post-traitement). Le core reste strictement tabulaire et déterministe.

## 1. Pré-traitement FITS natif

Objectif: extraire des features descriptives d'images FITS vers CSV sans modèle.
Exemples de features: flux total, centroid, FWHM approximatif.

Fichier:
- tools/optional/preprocess_fits.py

Activation (exemple):
python tools/optional/preprocess_fits.py --input "data/*.fits" --out-csv _ci_out/datasets/current.csv

Dépendance optionnelle:
- astropy

## 2. Gestion temporelle fine

Objectif: aligner des timestamps de manière descriptive.
Deux briques:
- phasage (phase_fold)
- correction barycentrique via astropy (barycentric_correct_jd)

Fichier:
- tools/optional/temporal_align.py

Dépendance optionnelle:
- astropy

## 3. Modélisation physique

Cette partie est plus interprétative par nature. Elle doit rester optionnelle et clairement séparée.
Exemples:
- Lomb-Scargle (détection de périodicité)
- transit model (batman)

Fichier:
- tools/optional/physical_model.py

Dépendances optionnelles:
- astropy
- batman-package

## 4. Parallélisme massif

Accélération purement technique, sans impact épistémique.
Implémentation minimale via stdlib.

Fichier:
- tools/optional/parallel_runner.py
