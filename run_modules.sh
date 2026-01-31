#!/usr/bin/env bash
set -euo pipefail

# BareFlux (bloc 4) : orchestration locale "côte à côte" + CI "modules/".
# Invariants:
# - Aucun lien vers le bloc 5.
# - Exécutable en GitHub Actions (checkout repos bloc 4 sous modules/).

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(cd "$REPO_DIR/.." && pwd)"

# 1) Déterminer où sont les 3 autres modules
if [ -d "$PARENT_DIR/RiftLens/src" ] && [ -d "$PARENT_DIR/NullTrace/src" ] && [ -d "$PARENT_DIR/VoidMark/src" ]; then
  MODULES_DIR="$PARENT_DIR"
elif [ -d "$REPO_DIR/modules/RiftLens/src" ] && [ -d "$REPO_DIR/modules/NullTrace/src" ] && [ -d "$REPO_DIR/modules/VoidMark/src" ]; then
  MODULES_DIR="$REPO_DIR/modules"
else
  echo "Modules introuvables. Attendu:"
  echo " - mode local:  $PARENT_DIR/{RiftLens,NullTrace,VoidMark}"
  echo " - mode CI:     $REPO_DIR/modules/{RiftLens,NullTrace,VoidMark}"
  exit 2
fi

DATASET_MULTI="${1:-$REPO_DIR/tests/data/test_multi.csv}"
DATASET_CURRENT="${2:-$REPO_DIR/tests/data/current.csv}"
DATASET_PREV="${3:-$REPO_DIR/tests/data/previous_shadow.csv}"

OUT_DIR="${4:-$REPO_DIR/_ci_out/run-all}"
mkdir -p "$OUT_DIR"

# 2) PYTHONPATH (exécution sans packaging)
export PYTHONPATH="$MODULES_DIR/RiftLens/src:$MODULES_DIR/NullTrace/src:$MODULES_DIR/VoidMark/src:$REPO_DIR/src:${PYTHONPATH:-}"

echo "BareFlux - Orchestration bloc 4"
echo "MODULES_DIR=$MODULES_DIR"
echo "OUT_DIR=$OUT_DIR"

# RiftLens
cd "$MODULES_DIR/RiftLens"
python -m riftlens "$DATASET_MULTI" --corr-threshold 0.6 --output-dir "$OUT_DIR/riftlens"

# NullTrace (2 étapes : snapshot previous puis snapshot current + diff)
cd "$MODULES_DIR/NullTrace"
python -m nulltrace snapshot "$DATASET_PREV" --output-dir "$OUT_DIR/nulltrace_prev"
PREV_MANIFEST="$(ls -t "$OUT_DIR/nulltrace_prev/shadows"/*/manifest.json | head -n 1)"

python -m nulltrace snapshot "$DATASET_CURRENT" --previous-shadow "$PREV_MANIFEST" --output-dir "$OUT_DIR/nulltrace_curr"

# VoidMark (marks sur graph_report.json RiftLens)
cd "$MODULES_DIR/VoidMark"
python -m voidmark "$OUT_DIR/riftlens/graph_report.json" --vault-dir "$OUT_DIR/vault"

echo "Tous les modules testés."
