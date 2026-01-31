#!/usr/bin/env bash
set -euo pipefail

# BareFlux (bloc 4) : orchestration locale "côte à côte" + CI "modules/".
# Invariants:
# - Aucun lien vers le bloc 5.
# - Exécutable en GitHub Actions (checkout repos bloc 4 sous modules/).
# - Chemins datasets et outputs en absolu pour éviter les erreurs de cwd.

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

# 2) Datasets: si non fournis, essayer d'abord _ci_out/datasets puis tests/data
default_multi=""
default_current=""
default_prev=""

if [ -f "$REPO_DIR/_ci_out/datasets/multi.csv" ]; then default_multi="$REPO_DIR/_ci_out/datasets/multi.csv"; fi
if [ -f "$REPO_DIR/_ci_out/datasets/current.csv" ]; then default_current="$REPO_DIR/_ci_out/datasets/current.csv"; fi
if [ -f "$REPO_DIR/_ci_out/datasets/previous_shadow.csv" ]; then default_prev="$REPO_DIR/_ci_out/datasets/previous_shadow.csv"; fi

if [ -z "$default_multi" ] && [ -f "$REPO_DIR/tests/data/multi.csv" ]; then default_multi="$REPO_DIR/tests/data/multi.csv"; fi
if [ -z "$default_current" ] && [ -f "$REPO_DIR/tests/data/current.csv" ]; then default_current="$REPO_DIR/tests/data/current.csv"; fi
if [ -z "$default_prev" ] && [ -f "$REPO_DIR/tests/data/previous_shadow.csv" ]; then default_prev="$REPO_DIR/tests/data/previous_shadow.csv"; fi

DATASET_MULTI="${1:-$default_multi}"
DATASET_CURRENT="${2:-$default_current}"
DATASET_PREV="${3:-$default_prev}"

OUT_DIR="${4:-$REPO_DIR/_ci_out/run-all}"
mkdir -p "$OUT_DIR"

# Validate inputs
if [ -z "$DATASET_MULTI" ] || [ ! -f "$DATASET_MULTI" ]; then
  echo "Dataset multi.csv introuvable."
  echo "Fourni: '$DATASET_MULTI'"
  echo "Attendu: _ci_out/datasets/multi.csv ou tests/data/multi.csv ou argument 1."
  exit 3
fi
if [ -z "$DATASET_CURRENT" ] || [ ! -f "$DATASET_CURRENT" ]; then
  echo "Dataset current.csv introuvable."
  echo "Fourni: '$DATASET_CURRENT'"
  echo "Attendu: _ci_out/datasets/current.csv ou tests/data/current.csv ou argument 2."
  exit 3
fi
if [ -z "$DATASET_PREV" ] || [ ! -f "$DATASET_PREV" ]; then
  echo "Dataset previous_shadow.csv introuvable."
  echo "Fourni: '$DATASET_PREV'"
  echo "Attendu: _ci_out/datasets/previous_shadow.csv ou tests/data/previous_shadow.csv ou argument 3."
  exit 3
fi

# Canonicalize to absolute paths
DATASET_MULTI="$(cd "$(dirname "$DATASET_MULTI")" && pwd)/$(basename "$DATASET_MULTI")"
DATASET_CURRENT="$(cd "$(dirname "$DATASET_CURRENT")" && pwd)/$(basename "$DATASET_CURRENT")"
DATASET_PREV="$(cd "$(dirname "$DATASET_PREV")" && pwd)/$(basename "$DATASET_PREV")"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

# 3) PYTHONPATH (exécution sans packaging)
export PYTHONPATH="$MODULES_DIR/RiftLens/src:$MODULES_DIR/NullTrace/src:$MODULES_DIR/VoidMark/src:$REPO_DIR/src:${PYTHONPATH:-}"

echo "BareFlux - Orchestration bloc 4"
echo "MODULES_DIR=$MODULES_DIR"
echo "DATASET_MULTI=$DATASET_MULTI"
echo "DATASET_PREV=$DATASET_PREV"
echo "DATASET_CURRENT=$DATASET_CURRENT"
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
