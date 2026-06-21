#!/usr/bin/env bash
set -euo pipefail

# BareFlux orchestrator (bloc 4)
# Usage:
#   ./run_modules.sh [--modules-dir DIR] [--out DIR] [--strict] [MULTI_CSV] [CURRENT_CSV] [PREVIOUS_CSV]
#
# In strict mode, BareFlux fails if any contractual artifact is missing:
#   riftlens/graph_report.json
#   nulltrace_prev/shadows/*/manifest.json
#   nulltrace_curr/shadows/*/manifest.json
#   nulltrace_curr/shadows/*/shadow_diff.json
#   vault/**/*
# It always writes bareflux_manifest.json after a completed orchestration phase.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODULES_DIR=""
OUT_DIR=""
STRICT="false"
PARALLEL="false"
CORR_THRESHOLD="0.6"

usage() {
  cat <<'EOF'
Usage: ./run_modules.sh [options] [MULTI_CSV] [CURRENT_CSV] [PREVIOUS_CSV]

Options:
  --modules-dir DIR      Directory containing RiftLens, NullTrace and VoidMark
  --out DIR              Output directory, default: _bareflux_out
  --output-dir DIR       Alias for --out
  --strict               Fail if expected artifacts are missing
  --corr-threshold N     RiftLens correlation threshold, default: 0.6
  --parallel             Accepted for compatibility, currently runs sequentially
  -h, --help             Show this help
EOF
}

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
    --corr-threshold)
      CORR_THRESHOLD="${2:-}"
      shift 2
      ;;
    --parallel)
      PARALLEL="true"
      shift 1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

if [ -z "$OUT_DIR" ]; then
  OUT_DIR="$REPO_DIR/_bareflux_out"
fi
if [ "${OUT_DIR:0:1}" != "/" ]; then
  OUT_DIR="$REPO_DIR/$OUT_DIR"
fi
mkdir -p "$OUT_DIR"

if [ -z "$MODULES_DIR" ]; then
  if [ -d "$REPO_DIR/modules/RiftLens/src" ]; then
    MODULES_DIR="$REPO_DIR/modules"
  else
    MODULES_DIR="$(cd "$REPO_DIR/.." && pwd)"
  fi
elif [ "${MODULES_DIR:0:1}" != "/" ]; then
  MODULES_DIR="$REPO_DIR/$MODULES_DIR"
fi

RIFT_DIR="$MODULES_DIR/RiftLens"
NT_DIR="$MODULES_DIR/NullTrace"
VM_DIR="$MODULES_DIR/VoidMark"

if [ ! -d "$RIFT_DIR/src" ] || [ ! -d "$NT_DIR/src" ] || [ ! -d "$VM_DIR/src" ]; then
  echo "Modules not found in MODULES_DIR=$MODULES_DIR" >&2
  echo "Expected: $MODULES_DIR/{RiftLens,NullTrace,VoidMark}/src" >&2
  exit 2
fi

MULTI_CSV="${1:-}"
CURRENT_CSV="${2:-}"
PREVIOUS_CSV="${3:-}"

DATASETS_DIR="$REPO_DIR/_ci_out/datasets"
mkdir -p "$DATASETS_DIR"

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

if [ "${MULTI_CSV:0:1}" != "/" ]; then MULTI_CSV="$REPO_DIR/$MULTI_CSV"; fi
if [ "${CURRENT_CSV:0:1}" != "/" ]; then CURRENT_CSV="$REPO_DIR/$CURRENT_CSV"; fi
if [ "${PREVIOUS_CSV:0:1}" != "/" ]; then PREVIOUS_CSV="$REPO_DIR/$PREVIOUS_CSV"; fi

export PYTHONPATH="$RIFT_DIR/src:$NT_DIR/src:$VM_DIR/src:$REPO_DIR/src:${PYTHONPATH:-}"

CURRENT_STEP="init"
write_failure_manifest() {
  local rc="$?"
  if [ "$rc" -ne 0 ]; then
    if [ "$STRICT" = "true" ]; then
      python -m bareflux.orchestration write-manifest \
        --out-dir "$OUT_DIR" \
        --modules-dir "$MODULES_DIR" \
        --multi-csv "$MULTI_CSV" \
        --current-csv "$CURRENT_CSV" \
        --previous-csv "$PREVIOUS_CSV" \
        --status FAIL \
        --failure-step "$CURRENT_STEP" \
        --strict >/dev/null 2>&1 || true
    else
      python -m bareflux.orchestration write-manifest \
        --out-dir "$OUT_DIR" \
        --modules-dir "$MODULES_DIR" \
        --multi-csv "$MULTI_CSV" \
        --current-csv "$CURRENT_CSV" \
        --previous-csv "$PREVIOUS_CSV" \
        --status FAIL \
        --failure-step "$CURRENT_STEP" >/dev/null 2>&1 || true
    fi
  fi
  exit "$rc"
}
trap write_failure_manifest EXIT

cat <<EOF
BareFlux - bloc 4 orchestration
MODULES_DIR=$MODULES_DIR
OUT_DIR=$OUT_DIR
MULTI_CSV=$MULTI_CSV
CURRENT_CSV=$CURRENT_CSV
PREVIOUS_CSV=$PREVIOUS_CSV
STRICT=$STRICT
PARALLEL=$PARALLEL
CORR_THRESHOLD=$CORR_THRESHOLD
EOF

CURRENT_STEP="riftlens"
mkdir -p "$OUT_DIR/riftlens"
python -m riftlens "$MULTI_CSV" --corr-threshold "$CORR_THRESHOLD" --output-dir "$OUT_DIR/riftlens"

CURRENT_STEP="nulltrace_previous"
mkdir -p "$OUT_DIR/nulltrace_prev" "$OUT_DIR/nulltrace_curr"
python -m nulltrace snapshot "$PREVIOUS_CSV" --output-dir "$OUT_DIR/nulltrace_prev"
PREV_MANIFEST="$(ls -t "$OUT_DIR/nulltrace_prev/shadows"/*/manifest.json | head -n 1)"

CURRENT_STEP="nulltrace_current"
python -m nulltrace snapshot "$CURRENT_CSV" --previous-shadow "$PREV_MANIFEST" --output-dir "$OUT_DIR/nulltrace_curr"

CURRENT_STEP="voidmark"
mkdir -p "$OUT_DIR/vault"
python -m voidmark "$OUT_DIR/riftlens/graph_report.json" --vault-dir "$OUT_DIR/vault"

CURRENT_STEP="manifest"
if [ "$STRICT" = "true" ]; then
  python -m bareflux.orchestration write-manifest \
    --out-dir "$OUT_DIR" \
    --modules-dir "$MODULES_DIR" \
    --multi-csv "$MULTI_CSV" \
    --current-csv "$CURRENT_CSV" \
    --previous-csv "$PREVIOUS_CSV" \
    --status PASS \
    --strict
else
  python -m bareflux.orchestration write-manifest \
    --out-dir "$OUT_DIR" \
    --modules-dir "$MODULES_DIR" \
    --multi-csv "$MULTI_CSV" \
    --current-csv "$CURRENT_CSV" \
    --previous-csv "$PREVIOUS_CSV" \
    --status PASS
fi

trap - EXIT
echo "BareFlux OK"
