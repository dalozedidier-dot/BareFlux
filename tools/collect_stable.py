from __future__ import annotations

import argparse
import json
import os
import subprocess
import statistics
from pathlib import Path
from typing import Dict, Any, List

def run_cmd(cmd: List[str], cwd: Path, env: Dict[str, str] | None = None) -> None:
    p = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            f"cmd_failed rc={p.returncode}\n"
            f"cmd={' '.join(cmd)}\n"
            f"stdout=\n{p.stdout}\n"
            f"stderr=\n{p.stderr}"
        )

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def edge_set_from_report(report_path: Path) -> set[tuple[str, str]]:
    obj = load_json(report_path)
    edges = obj.get("edges", [])
    out: set[tuple[str, str]] = set()
    for e in edges:
        a = str(e.get("source"))
        b = str(e.get("target"))
        out.add((a, b) if a <= b else (b, a))
    return out

def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    u = a | b
    return 1.0 if not u else len(a & b) / len(u)

def extract_nulltrace_abs_deltas(diff_path: Path) -> List[float]:
    diff_obj = load_json(diff_path)
    diff = diff_obj.get("diff", {})
    col_changes = diff.get("column_changes", {})
    values: List[float] = []
    for _, ch in col_changes.items():
        deltas = (ch or {}).get("deltas", {}) or {}
        for _, v in deltas.items():
            try:
                values.append(abs(float(v)))
            except Exception:
                pass
    return values

def quantiles(xs: List[float]) -> Dict[str, float]:
    if not xs:
        return {"p50": 0.0, "p90": 0.0, "p99": 0.0, "mad": 0.0, "n": 0}
    xs2 = sorted(xs)
    def q(p: float) -> float:
        i = int(round((len(xs2) - 1) * p))
        return float(xs2[i])
    med = statistics.median(xs2)
    mad = statistics.median([abs(x - med) for x in xs2])
    return {"p50": float(med), "p90": q(0.90), "p99": q(0.99), "mad": float(mad), "n": int(len(xs2))}

def main() -> None:
    p = argparse.ArgumentParser(description="Collecte stabilité bloc 4 (web-only via Actions).")
    p.add_argument("--thresholds", type=str, default="0.50,0.60,0.70,0.75,0.80")
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--out-dir", type=str, default="_ci_out/stability")
    p.add_argument("--datasets-dir", type=str, default="_ci_out/datasets")
    args = p.parse_args()

    repo_dir = Path(__file__).resolve().parents[1]
    modules_dir = repo_dir / "modules"
    rift = modules_dir / "RiftLens"
    nt = modules_dir / "NullTrace"
    vm = modules_dir / "VoidMark"

    out = (repo_dir / args.out_dir).resolve() if not Path(args.out_dir).is_absolute() else Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    datasets = (repo_dir / args.datasets_dir).resolve() if not Path(args.datasets_dir).is_absolute() else Path(args.datasets_dir).resolve()
    multi_csv = (datasets / "multi.csv").resolve()
    prev_csv = (datasets / "previous_shadow.csv").resolve()
    curr_csv = (datasets / "current.csv").resolve()

    if not multi_csv.exists():
        raise FileNotFoundError(f"multi.csv missing: {multi_csv}")
    if not prev_csv.exists():
        raise FileNotFoundError(f"previous_shadow.csv missing: {prev_csv}")
    if not curr_csv.exists():
        raise FileNotFoundError(f"current.csv missing: {curr_csv}")

    thresholds = [float(x.strip()) for x in args.thresholds.split(",") if x.strip()]
    k = int(args.k)

    env = dict(os.environ)
    env["PYTHONPATH"] = ":".join([
        str(rift / "src"),
        str(nt / "src"),
        str(vm / "src"),
        str(repo_dir / "src"),
        env.get("PYTHONPATH", ""),
    ]).strip(":")

    report: Dict[str, Any] = {
        "tool": "BareFlux.collect-stable",
        "thresholds": thresholds,
        "k": k,
        "results": {},
    }

    for thr in thresholds:
        thr_key = f"{thr:.2f}"
        thr_dir = (out / f"thr_{thr_key}").resolve()
        thr_dir.mkdir(parents=True, exist_ok=True)

        edge_sets: List[set[tuple[str,str]]] = []
        nt_deltas_all: List[float] = []
        marks_counts: List[int] = []

        for i in range(1, k + 1):
            run_dir = (thr_dir / f"run_{i:02d}").resolve()
            run_dir.mkdir(parents=True, exist_ok=True)

            # RiftLens
            r_out = (run_dir / "riftlens").resolve()
            r_out.mkdir(parents=True, exist_ok=True)
            run_cmd(
                ["python", "-m", "riftlens", str(multi_csv), "--corr-threshold", str(thr), "--output-dir", str(r_out)],
                cwd=rift,
                env=env,
            )
            edge_sets.append(edge_set_from_report(r_out / "graph_report.json"))

            # NullTrace prev -> curr (diff)
            nt_prev = (run_dir / "nulltrace_prev").resolve()
            nt_curr = (run_dir / "nulltrace_curr").resolve()
            nt_prev.mkdir(parents=True, exist_ok=True)
            nt_curr.mkdir(parents=True, exist_ok=True)

            run_cmd(["python", "-m", "nulltrace", "snapshot", str(prev_csv), "--output-dir", str(nt_prev)], cwd=nt, env=env)
            manifests = sorted((nt_prev / "shadows").glob("*/manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            prev_manifest = manifests[0]

            run_cmd(
                ["python", "-m", "nulltrace", "snapshot", str(curr_csv), "--previous-shadow", str(prev_manifest), "--output-dir", str(nt_curr)],
                cwd=nt,
                env=env,
            )
            diffs = sorted((nt_curr / "shadows").glob("*/shadow_diff.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if diffs:
                nt_deltas_all.extend(extract_nulltrace_abs_deltas(diffs[0]))

            # VoidMark
            v_out = (run_dir / "vault").resolve()
            v_out.mkdir(parents=True, exist_ok=True)
            run_cmd(["python", "-m", "voidmark", str(r_out / "graph_report.json"), "--vault-dir", str(v_out)], cwd=vm, env=env)
            marks_counts.append(len(list(v_out.rglob("*.json"))) + len(list(v_out.rglob("*.md"))) + len(list(v_out.rglob("*.txt"))))

        base_edges = edge_sets[0] if edge_sets else set()
        j_list = [jaccard(base_edges, es) for es in edge_sets[1:]] if len(edge_sets) > 1 else [1.0]
        report["results"][thr_key] = {
            "riftlens": {
                "n_edges_runs": [len(es) for es in edge_sets],
                "jaccard_vs_run1": j_list,
                "jaccard_median": float(statistics.median(j_list)) if j_list else 1.0,
            },
            "nulltrace": {
                "abs_delta_stats": quantiles(nt_deltas_all),
            },
            "voidmark": {
                "marks_files_count_runs": marks_counts,
                "marks_files_count_median": float(statistics.median(marks_counts)) if marks_counts else 0.0,
            },
        }

    (out / "stability_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"stability_report={ (out / 'stability_report.json').resolve() }")

if __name__ == "__main__":
    main()
