#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "BareFlux - Test rapide"

cd "$ROOT_DIR/RiftLens"
python src/rift_lens.py tests/data/test_multi.csv --corr-threshold 0.6 --output-dir outputs

cd "$ROOT_DIR/NullTrace"
python src/null_trace.py tests/data/current.csv --previous-shadow tests/data/previous_shadow.csv --output-dir outputs

cd "$ROOT_DIR/VoidMark"
python src/void_mark.py "$ROOT_DIR/RiftLens/outputs/graph_report.json" --vault-dir vault_test

echo "Tous les modules testés."
