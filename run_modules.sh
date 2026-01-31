#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "BareFlux - Test rapide"

# Mode CI: modules/...
# Mode local (dossier racine GitHub PC): ../RiftLens, ../NullTrace, ../VoidMark
if [ -d "$REPO_DIR/modules/RiftLens" ]; then
  BASE_DIR="$REPO_DIR/modules"
else
  BASE_DIR="$(cd "$REPO_DIR/.." && pwd)"
fi

cd "$BASE_DIR/RiftLens"
PYTHONPATH=src python src/rift_lens.py tests/data/test_multi.csv --corr-threshold 0.6 --output-dir outputs

cd "$BASE_DIR/NullTrace"
PYTHONPATH=src python src/null_trace.py tests/data/current.csv --previous-shadow tests/data/previous_shadow.csv --output-dir outputs

cd "$BASE_DIR/VoidMark"
PYTHONPATH=src python src/void_mark.py "$BASE_DIR/RiftLens/outputs/graph_report.json" --vault-dir vault_test

echo "Tous les modules testés."
