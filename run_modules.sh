#!/usr/bin/env bash
set -euo pipefail

# BareFlux orchestrator (bloc 4)
# Supports CI call style: ./run_modules.sh --modules-dir modules --out _bareflux_out --strict
# Also supports positional datasets after options:
#   ./run_modules.sh [--modules-dir DIR] [--out DIR] [--strict] [MULTI_CSV] [CURRENT_CSV] [PREVIOUS_CSV]

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODULES_DIR=""
OUT_DIR=""
STRICT="false"

# -------- option parsing --------
while [ $# -gt 0 ]; do
  case "$1" in
    --modules-dir)
      MODULES_DIR="${2:-}"
      shift 2
      ;;
    --out|--output-dir)
      OUT_DIR="${2:-}"
      shift 2
      ;;
    --strict)
      STRICT="true"
      shift 1
      ;;
    --help|-h)
      echo "Usage: ./run_modules.sh [--modules-dir DIR] [--out DIR] [--strict] [MULTI_CSV] [CURRENT_CSV] [PREVIOUS_CSV]"
      exit 0
      ;;
    --*)
      echo "Option inconnue: $1"
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

# -------- defaults --------
if [ -z "$OUT_DIR" ]; then
  OUT_DIR="$REPO_DIR/_bareflux_out"
fi
mkdir -p "$OUT_DIR"

# modules dir resolution:
# - CI: REPO_DIR/modules
# - local: parent dir containing siblings RiftLens/NullTrace/VoidMark
if [ -z "$MODULES_DIR" ]; then
  if [ -d "$REPO_DIR/modules/RiftLens/src" ]; then
    MODULES_DIR="$REPO_DIR/modules"
  else
    MODULES_DIR="$(cd "$REPO_DIR/.." && pwd)"
  fi
else
  # allow relative path
  if [ "${MODULES_DIR:0:1}" != "/" ]; then
    MODULES_DIR="$REPO_DIR/$MODULES_DIR"
  fi
fi

RIFT_DIR="$MODULES_DIR/RiftLens"
NT_DIR="$MODULES_DIR/NullTrace"
VM_DIR="$MODULES_DIR/VoidMark"

if [ ! -d "$RIFT_DIR/src" ] || [ ! -d "$NT_DIR/src" ] || [ ! -d "$VM_DIR/src" ]; then
  echo "Modules introuvables dans MODULES_DIR=$MODULES_DIR"
  echo "Attendu: $MODULES_DIR/{RiftLens,NullTrace,VoidMark}/src"
  exit 2
fi

# -------- datasets (positional) --------
MULTI_CSV="${1:-}"
CURRENT_CSV="${2:-}"
PREVIOUS_CSV="${3:-}"

DATASETS_DIR="$REPO_DIR/_ci_out/datasets"
mkdir -p "$DATASETS_DIR"

# If any dataset is missing, auto-generate into _ci_out/datasets/
need_gen="false"
if [ -z "$MULTI_CSV" ] || [ ! -f "$MULTI_CSV" ]; then need_gen="true"; fi
if [ -z "$CURRENT_CSV" ] || [ ! -f "$CURRENT_CSV" ]; then need_gen="true"; fi
if [ -z "$PREVIOUS_CSV" ] || [ ! -f "$PREVIOUS_CSV" ]; then need_gen="true"; fi

if [ "$need_gen" = "true" ]; then
  python "$REPO_DIR/tools/generate_synth_datasets.py" --out-dir "$DATASETS_DIR" --n 200 --seed 42
  MULTI_CSV="$DATASETS_DIR/multi.csv"
  CURRENT_CSV="$DATASETS_DIR/current.csv"
  PREVIOUS_CSV="$DATASETS_DIR/previous_shadow.csv"
fi

# Resolve relative paths (if provided)
if [ "${MULTI_CSV:0:1}" != "/" ]; then MULTI_CSV="$REPO_DIR/$MULTI_CSV"; fi
if [ "${CURRENT_CSV:0:1}" != "/" ]; then CURRENT_CSV="$REPO_DIR/$CURRENT_CSV"; fi
if [ "${PREVIOUS_CSV:0:1}" != "/" ]; then PREVIOUS_CSV="$REPO_DIR/$PREVIOUS_CSV"; fi

if [ ! -f "$MULTI_CSV" ]; then
  echo "Dataset multi.csv introuvable."
  echo "Fourni: '${1:-<vide>}'"
  echo "Attendu: _ci_out/datasets/multi.csv ou tests/data/multi.csv ou argument MULTI_CSV."
  exit 3
fi

# -------- PYTHONPATH --------
export PYTHONPATH="$RIFT_DIR/src:$NT_DIR/src:$VM_DIR/src:$REPO_DIR/src:${PYTHONPATH:-}"

echo "BareFlux - Orchestration bloc 4"
echo "MODULES_DIR=$MODULES_DIR"
echo "OUT_DIR=$OUT_DIR"
echo "MULTI_CSV=$MULTI_CSV"
echo "CURRENT_CSV=$CURRENT_CSV"
echo "PREVIOUS_CSV=$PREVIOUS_CSV"
echo "STRICT=$STRICT"

# -------- run RiftLens --------
mkdir -p "$OUT_DIR/riftlens"
python -m riftlens "$MULTI_CSV" --corr-threshold 0.6 --output-dir "$OUT_DIR/riftlens"

# -------- run NullTrace prev -> current --------
mkdir -p "$OUT_DIR/nulltrace_prev" "$OUT_DIR/nulltrace_curr"
python -m nulltrace snapshot "$PREVIOUS_CSV" --output-dir "$OUT_DIR/nulltrace_prev"
PREV_MANIFEST="$(ls -t "$OUT_DIR/nulltrace_prev/shadows"/*/manifest.json | head -n 1)"
python -m nulltrace snapshot "$CURRENT_CSV" --previous-shadow "$PREV_MANIFEST" --output-dir "$OUT_DIR/nulltrace_curr"

# -------- run VoidMark --------
mkdir -p "$OUT_DIR/vault"
python -m voidmark "$OUT_DIR/riftlens/graph_report.json" --vault-dir "$OUT_DIR/vault"

echo "OK"
