BareFlux — patch CI postprocess (skip-if-missing)
Date: 2026-02-03

Problème (logs_56222525936.zip):
  - python tools/bareflux_postprocess.py --out _bareflux_out --inplace
  - => shadow_diff.json introuvable sous _bareflux_out (exit 1)

Correctif:
  - Ajout/usage de --skip-if-missing
  - Le workflow et le snippet CI fournis appellent déjà:
      python tools/bareflux_postprocess.py --out _bareflux_out --inplace --skip-if-missing

Installation:
  - Dézippe à la racine du repo BareFlux.
  - Commit + push.

Impact:
  - Les runs "workflow_dispatch" ne cassent plus si _bareflux_out est absent.
  - Le comportement strict reste disponible en omettant --skip-if-missing.
