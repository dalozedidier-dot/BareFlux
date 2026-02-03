Patch minimal — workflow + postprocess (skip-if-missing)
Date: 2026-02-03

But:
  - Empêcher un échec si _bareflux_out/**/shadow_diff.json est absent.
  - Le workflow appelle: python tools/bareflux_postprocess.py ... --skip-if-missing

Installation:
  1) Dézippe à la racine du repo BareFlux
  2) Commit + push sur la branche que tu déclenches via workflow_dispatch (ex: main)

Vérification (dans les logs):
  - La commande doit contenir: --skip-if-missing
  - Dans system.txt: "Job defined at: .../.github/workflows/bareflux-improvements.yml@refs/heads/<branche>"
