# BareFlux v0.2.1 notes

This hotfix addresses the CI logs where GitHub was still running stale files from the old ApexObserver layout.

## Log diagnosis

- `run-all.yml` was still present and called `./run_modules.sh`, causing `Permission denied` when the executable bit was not preserved.
- `src/apexobserver/` was still present, so `black --check src ...` formatted the old package instead of the cleaned BareFlux package only.

## Fixes

- `orchestrate.yml` now calls `bash run_modules.sh` and no longer depends on the executable bit.
- `ci.yml` checks `src/bareflux`, `tests`, `tools`, and `examples` explicitly.
- A compatibility `run-all.yml` is included so an old stale workflow is overwritten if the ZIP is copied over an existing repository.
- Removed stale ApexObserver paths from the repository and kept
  `scripts/cleanup_obsolete_bareflux_files.sh` as an idempotent helper for
  ZIP-overlay updates.

## Cleanup when updating by ZIP overlay

If an update is applied by copying a ZIP over an existing checkout, run this
once from the repo root before committing:

```bash
bash scripts/cleanup_obsolete_bareflux_files.sh
git status
```

Then commit all modifications and deletions.
