BareFlux — Improvements (ALL-IN-ONE) — v3.1.0
Date: 2026-02-03

Où ça va ?
  -> Dézippe ce zip à la RACINE du repo BareFlux.

Pourquoi le workflow a cassé (logs_56222298002.zip) ?
  - postprocess a été exécuté sans outputs: `_bareflux_out/**/shadow_diff.json` absent.
  - Correctif: `--skip-if-missing` (déjà activé dans snippets + workflow exemple).

Activation minimale (CI):
  - Après `bareflux orchestrate ...`, colle:
      ci_snippets/github_actions_steps.yml

Contenu:
  - tools/      : postprocess + score drift + lisibilité b + dédup + monitoring + insight + advanced
  - examples/   : scripts démo (console / notebook) + mini rapport Markdown
  - .github/    : workflow exemple (manual dispatch)
