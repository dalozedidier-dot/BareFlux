#!/usr/bin/env bash
set -euo pipefail

# Cleanup helper for the BareFlux v0.2.x identity migration.
# Run from the repository root. It removes stale ApexObserver files and obsolete workflows
# that remain when the ZIP is copied over the repo instead of replacing it cleanly.

rm -rf apexobserver
rm -rf src/apexobserver
rm -rf ApexObserver.egg-info
rm -f examples/apex.json
rm -f configs/apex_default.json
rm -f .github/workflows/bareflux-improvements.yml

# Keep run-all.yml as a compatibility workflow if present in v0.2.1+.
# The canonical workflows are ci.yml, orchestrate.yml, collect-stable.yml and mass-collect.yml.

# GitHub web uploads can lose the executable bit. Workflows call bash run_modules.sh,
# but setting the bit locally is still useful for manual runs.
chmod +x run_modules.sh 2>/dev/null || true

echo "BareFlux obsolete-file cleanup complete."
