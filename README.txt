BareFlux — Improvements (ALL-IN-ONE)
Date: 2026-02-03
Version: v0.2.0

Où ça va ?
  -> Tu dézippes CE ZIP À LA RACINE du repo BareFlux (même niveau que pyproject.toml / src/ / .github/).

Ce que ça ajoute :
  - tools/ : scripts post-process & insight
  - ci_snippets/ : steps GitHub Actions prêts à coller
  - .github/workflows/bareflux-improvements.yml : exemple (workflow_dispatch)

Activation minimale (recommandée) :
  1) Dézip à la racine
  2) Dans ton workflow CI (après `bareflux orchestrate ...`), colle les steps du fichier :
       ci_snippets/github_actions_steps.yml

Low-hanging fruit couvert :
  - Fix n_edges incohérent (patch dans le summary)
  - Dédup dd_graph_artifacts*.zip (SHA256)
  - Score drift global (green/yellow/red) via score_effective_v1
  - Colonne b : IQR/MAD + %(|delta| > seuil)

Optionnel :
  - Medium insight: VoidMark distances + RiftLens sweep + stabilité
  - Monitoring longitudinal: history JSONL + trend CSV
  - Advanced: IsolationForest (si scikit-learn) + mini HTML report

Exemples (démonstration / article) :
  - examples/README.md
  - examples/extract_and_print.py
  - examples/make_report_md.py
