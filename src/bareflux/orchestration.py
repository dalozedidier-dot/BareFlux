from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODULE_NAMES = ("RiftLens", "NullTrace", "VoidMark")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def git_sha(path: Path) -> str:
    try:
        p = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if p.returncode == 0:
            return p.stdout.strip()
    except Exception:
        pass
    return ""


def rel_or_abs(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return str(path.resolve())


def file_entry(path: Path, root: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {"path": rel_or_abs(path, root), "exists": False, "sha256": ""}
    return {
        "path": rel_or_abs(path, root),
        "exists": True,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def newest(paths: list[Path]) -> Path | None:
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    return sorted(existing, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def discover_outputs(out_dir: Path) -> dict[str, Any]:
    rift_report = out_dir / "riftlens" / "graph_report.json"
    nt_prev_manifest = newest(
        list((out_dir / "nulltrace_prev" / "shadows").glob("*/manifest.json"))
    )
    nt_curr_manifest = newest(
        list((out_dir / "nulltrace_curr" / "shadows").glob("*/manifest.json"))
    )
    nt_curr_diff = newest(
        list((out_dir / "nulltrace_curr" / "shadows").glob("*/shadow_diff.json"))
    )
    vault_files = sorted([p for p in (out_dir / "vault").rglob("*") if p.is_file()])

    return {
        "riftlens": {"graph_report": rift_report},
        "nulltrace": {
            "previous_manifest": nt_prev_manifest,
            "current_manifest": nt_curr_manifest,
            "current_diff": nt_curr_diff,
        },
        "voidmark": {"vault_files": vault_files},
    }


def strict_errors(out_dir: Path) -> list[str]:
    outputs = discover_outputs(out_dir)
    errors: list[str] = []

    if not outputs["riftlens"]["graph_report"].exists():
        errors.append("missing:rftlens_graph_report:riftlens/graph_report.json")

    nt = outputs["nulltrace"]
    if nt["previous_manifest"] is None:
        errors.append(
            "missing:nulltrace_previous_manifest:nulltrace_prev/shadows/*/manifest.json"
        )
    if nt["current_manifest"] is None:
        errors.append(
            "missing:nulltrace_current_manifest:nulltrace_curr/shadows/*/manifest.json"
        )
    if nt["current_diff"] is None:
        errors.append(
            "missing:nulltrace_current_diff:nulltrace_curr/shadows/*/shadow_diff.json"
        )

    if not outputs["voidmark"]["vault_files"]:
        errors.append("missing:voidmark_vault_files:vault/**/*")

    return errors


def module_metadata(modules_dir: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    for name in MODULE_NAMES:
        path = modules_dir / name
        meta[name.lower()] = {
            "path": str(path),
            "src_exists": (path / "src").exists(),
            "git_sha": git_sha(path) if path.exists() else "",
        }
    return meta


def build_manifest(
    out_dir: Path,
    modules_dir: Path,
    datasets: dict[str, Path],
    status: str,
    strict: bool,
    failure_step: str = "",
) -> dict[str, Any]:
    root = out_dir.resolve()
    outputs = discover_outputs(out_dir)
    errors = strict_errors(out_dir) if strict else []
    final_status = "FAIL" if errors or status.upper() == "FAIL" else "PASS"

    nt = outputs["nulltrace"]
    manifest: dict[str, Any] = {
        "schema_version": "bareflux.manifest.v1",
        "tool": "BareFlux",
        "version": "0.2.0",
        "created_at_utc": utc_now(),
        "status": final_status,
        "strict": bool(strict),
        "failure_step": failure_step,
        "github_sha": os.environ.get("GITHUB_SHA", ""),
        "modules_dir": str(modules_dir.resolve()),
        "modules": module_metadata(modules_dir),
        "datasets": {
            key: file_entry(path, root) for key, path in sorted(datasets.items())
        },
        "outputs": {
            "riftlens": {
                "graph_report": file_entry(outputs["riftlens"]["graph_report"], root)
            },
            "nulltrace": {
                "previous_manifest": (
                    file_entry(nt["previous_manifest"], root)
                    if nt["previous_manifest"] is not None
                    else {"exists": False, "path": "", "sha256": ""}
                ),
                "current_manifest": (
                    file_entry(nt["current_manifest"], root)
                    if nt["current_manifest"] is not None
                    else {"exists": False, "path": "", "sha256": ""}
                ),
                "current_diff": (
                    file_entry(nt["current_diff"], root)
                    if nt["current_diff"] is not None
                    else {"exists": False, "path": "", "sha256": ""}
                ),
            },
            "voidmark": {
                "vault_file_count": len(outputs["voidmark"]["vault_files"]),
                "vault_files": [
                    file_entry(p, root)
                    for p in outputs["voidmark"]["vault_files"][:200]
                ],
            },
        },
        "strict_errors": errors,
    }
    return manifest


def write_manifest_from_args(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    modules_dir = Path(args.modules_dir).resolve()
    datasets = {
        "multi_csv": Path(args.multi_csv).resolve() if args.multi_csv else Path(""),
        "current_csv": (
            Path(args.current_csv).resolve() if args.current_csv else Path("")
        ),
        "previous_csv": (
            Path(args.previous_csv).resolve() if args.previous_csv else Path("")
        ),
    }
    manifest = build_manifest(
        out_dir=out_dir,
        modules_dir=modules_dir,
        datasets=datasets,
        status=args.status,
        strict=args.strict,
        failure_step=args.failure_step or "",
    )
    out_path = out_dir / "bareflux_manifest.json"
    write_json(out_path, manifest)
    print(f"bareflux_manifest={out_path}")
    if args.strict and manifest["strict_errors"]:
        for err in manifest["strict_errors"]:
            print(err, file=sys.stderr)
        return 1
    return 0


def strict_check_from_args(args: argparse.Namespace) -> int:
    errors = strict_errors(Path(args.out_dir).resolve())
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    else:
        if errors:
            print("Strict check failed:")
            for err in errors:
                print(f"- {err}")
        else:
            print("Strict check passed")
    return 1 if errors else 0


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    n = len(values)
    mid = n // 2
    if n % 2:
        return float(values[mid])
    return float((values[mid - 1] + values[mid]) / 2)


def summarize_stability(path: Path) -> dict[str, Any]:
    obj = read_json(path)
    rows: list[dict[str, Any]] = []
    for threshold, data in sorted((obj.get("results") or {}).items()):
        rift = data.get("riftlens") or {}
        nt = data.get("nulltrace") or {}
        vm = data.get("voidmark") or {}
        rows.append(
            {
                "threshold": threshold,
                "riftlens_edges_median": _median(
                    [float(x) for x in rift.get("n_edges_runs", [])]
                ),
                "riftlens_jaccard_median": float(rift.get("jaccard_median", 0.0)),
                "nulltrace_abs_delta_p50": float(
                    (nt.get("abs_delta_stats") or {}).get("p50", 0.0)
                ),
                "nulltrace_abs_delta_p90": float(
                    (nt.get("abs_delta_stats") or {}).get("p90", 0.0)
                ),
                "voidmark_files_median": float(vm.get("marks_files_count_median", 0.0)),
            }
        )
    return {
        "source": str(path),
        "threshold_count": len(rows),
        "rows": rows,
    }


def mass_overview_from_args(args: argparse.Namespace) -> int:
    mass_dir = Path(args.mass_dir).resolve()
    out_json = Path(args.out_json).resolve()
    out_csv = Path(args.out_csv).resolve() if args.out_csv else None
    run_reports = sorted(mass_dir.glob("run_*/stability/stability_report.json"))

    run_summaries: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []
    for report_path in run_reports:
        run_id = report_path.parents[1].name
        summary = summarize_stability(report_path)
        run_rows = summary["rows"]
        jaccards = [float(r["riftlens_jaccard_median"]) for r in run_rows]
        p90s = [float(r["nulltrace_abs_delta_p90"]) for r in run_rows]
        vm_counts = [float(r["voidmark_files_median"]) for r in run_rows]
        run_summaries.append(
            {
                "run_id": run_id,
                "report": str(report_path),
                "threshold_count": len(run_rows),
                "jaccard_median_across_thresholds": _median(jaccards),
                "nulltrace_p90_median_across_thresholds": _median(p90s),
                "voidmark_files_median_across_thresholds": _median(vm_counts),
            }
        )
        for row in run_rows:
            flat = {"run_id": run_id}
            flat.update(row)
            flat_rows.append(flat)

    overview = {
        "schema_version": "bareflux.mass_collect_overview.v1",
        "created_at_utc": utc_now(),
        "mass_dir": str(mass_dir),
        "run_count": len(run_summaries),
        "runs": run_summaries,
        "aggregate": {
            "jaccard_median_all_runs": _median(
                [float(r["jaccard_median_across_thresholds"]) for r in run_summaries]
            ),
            "nulltrace_p90_median_all_runs": _median(
                [
                    float(r["nulltrace_p90_median_across_thresholds"])
                    for r in run_summaries
                ]
            ),
            "voidmark_files_median_all_runs": _median(
                [
                    float(r["voidmark_files_median_across_thresholds"])
                    for r in run_summaries
                ]
            ),
        },
    }
    write_json(out_json, overview)
    print(f"mass_collect_overview={out_json}")

    if out_csv is not None:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        if flat_rows:
            fields = list(flat_rows[0].keys())
            with out_csv.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(flat_rows)
        else:
            out_csv.write_text("run_id\n", encoding="utf-8")
        print(f"mass_collect_summary={out_csv}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m bareflux.orchestration")
    sub = parser.add_subparsers(dest="cmd", required=True)

    write = sub.add_parser("write-manifest")
    write.add_argument("--out-dir", required=True)
    write.add_argument("--modules-dir", required=True)
    write.add_argument("--multi-csv", default="")
    write.add_argument("--current-csv", default="")
    write.add_argument("--previous-csv", default="")
    write.add_argument("--status", default="PASS", choices=["PASS", "FAIL"])
    write.add_argument("--failure-step", default="")
    write.add_argument("--strict", action="store_true")
    write.set_defaults(func=write_manifest_from_args)

    check = sub.add_parser("strict-check")
    check.add_argument("--out-dir", required=True)
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=strict_check_from_args)

    mass = sub.add_parser("mass-overview")
    mass.add_argument("--mass-dir", required=True)
    mass.add_argument("--out-json", required=True)
    mass.add_argument("--out-csv", default="")
    mass.set_defaults(func=mass_overview_from_args)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
