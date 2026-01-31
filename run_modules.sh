#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# -------------------------------------------------------------------
# BareFlux orchestration script
# - Exécute RiftLens, NullTrace, VoidMark dans un workspace commun
# - Fonctionne en local (repos côte à côte) ET en CI (repos dans le repo root)
# -------------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Détecte l'emplacement des repos (local: parent de BareFlux ; CI: dans BareFlux)
WORKSPACE_CANDIDATES=(
  "$(dirname "$ROOT_DIR")"
  "$ROOT_DIR"
)

WORKSPACE=""
for cand in "${WORKSPACE_CANDIDATES[@]}"; do
  if [[ -d "$cand/RiftLens" && -d "$cand/NullTrace" && -d "$cand/VoidMark" && -d "$cand/BareFlux" ]]; then
    WORKSPACE="$cand"
    break
  fi
done

if [[ -z "$WORKSPACE" ]]; then
  echo "[BareFlux] Workspace non conforme."
  echo "Attendu (au choix) :"
  echo "  - parent_dir/{BareFlux,RiftLens,NullTrace,VoidMark}"
  echo "  - BareFlux/{BareFlux,RiftLens,NullTrace,VoidMark} (CI)"
  exit 2
fi

echo "[BareFlux] Workspace: $WORKSPACE"

run_in_repo() {
  local repo="$1"
  shift
  echo ""
  echo "[BareFlux] >>> ${repo}"
  ( cd "$WORKSPACE/$repo" && "$@" )
}

# RiftLens
run_in_repo "RiftLens"   python src/rift_lens.py tests/data/test_multi.csv --corr-threshold 0.6 --output-dir outputs

# NullTrace
run_in_repo "NullTrace"   python src/null_trace.py tests/data/current.csv --previous-shadow tests/data/previous_shadow.csv --output-dir outputs

# VoidMark
run_in_repo "VoidMark" bash -lc '
  mkdir -p tmp_run
  echo '"'"'{"test": "block1"}'"'"' > tmp_run/test.json
  python src/void_mark.py tmp_run/test.json --vault-dir vault_test
'

echo ""
echo "[BareFlux] OK"
