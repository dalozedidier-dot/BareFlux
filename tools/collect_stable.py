from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def run_cmd(cmd: List[str], cwd: Path, env: Dict[str, str] | None = None) -> None:
    p = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            "cmd_failed rc=%s\ncmd=%s\nstdout=\n%s\nstderr=\n%s"
            % (p.returncode, " ".join(cmd), p.stdout, p.stderr)
        )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    for _, ch in (col_changes or {}).items():
        deltas = (ch or {}).get("deltas", {}) or {}
        for _, v in deltas.items():
            try:
                values.append(abs(float(v)))
            except Exception:
                pass
    return values


def quantiles(xs: List[float]) -> Dict[str, float | int]:
    if not xs:
        return {"p50": 0.0, "p90": 0.0, "p99": 0.0, "mad": 0.0, "n": 0}
    xs2 = sorted(xs)

    def q(p: float) -> float:
        i = int(round((len(xs2) - 1) * p))
        return float(xs2[i])

    med = statistics.median(xs2)
    mad = statistics.median([abs(x - med) for x in xs2])
    return {"p50": float(med), "p90": q(0.90), "p99": q(0.99), "mad": float(mad), "n": int(len(xs2))}


def _resolve_under_repo(repo_dir: Path, p: Path) -> Path:
    # Rend les chemins robustes si l'étape Actions change de cwd.
    return (p if p.is_absolute() else (repo_dir / p)).resolve()


def _assert_exists(path: Path, label: str, hint_dir: Path | None = None) -> None:
    if path.exists():
        return
    lines = [f"missing={label}", f"path={path}"]
    if hint_dir is not None:
        lines.append(f"hint_dir={hint_dir}")
        if hint_dir.exists():
            try:
                listing = sorted([x.name for x in hint_dir.iterdir()])
                lines.append("hint_dir_listing=" + ", ".join(listing))
            except Exception:
                lines.append("hint_dir_listing=<error>")
        else:
            lines.append("hint_dir_listing=<dir_missing>")
    raise FileNotFoundError("\n".join(lines))


def main() -> None:
    p = argparse.ArgumentParser(description="Collecte stabilité bloc 4 (Mode A).")
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

    out = _resolve_under_repo(repo_dir, Path(args.out_dir))
    out.mkdir(parents=True, exist_ok=True)

    datasets = _resolve_under_repo(repo_dir, Path(args.datasets_dir))
    multi_csv = (datasets / "multi.csv").resolve()
    prev_csv = (datasets / "previous_shadow.csv").resolve()
    curr_csv = (datasets / "current.csv").resolve()

    _assert_exists(datasets, "datasets_dir", hint_dir=repo_dir / "_ci_out")
    _assert_exists(multi_csv, "multi.csv", hint_dir=datasets)
    _assert_exists(prev_csv, "previous_shadow.csv", hint_dir=datasets)
    _assert_exists(curr_csv, "current.csv", hint_dir=datasets)

    thresholds = [float(x.strip()) for x in args.thresholds.split(",") if x.strip()]
    k = int(args.k)

    env = dict(os.environ)
    env["PYTHONPATH"] = ":".join(
        [
            str((rift / "src").resolve()),
            str((nt / "src").resolve()),
            str((vm / "src").resolve()),
            str((repo_dir / "src").resolve()),
            env.get("PYTHONPATH", ""),
        ]
    ).strip(":")

    report: Dict[str, Any] = {
        "tool": "BareFlux.collect-stable",
        "mode": "A",
        "git_sha": env.get("GITHUB_SHA", ""),
        "thresholds": thresholds,
        "k": k,
        "datasets": {
            "multi.csv": {"path": str(multi_csv), "sha256": sha256_file(multi_csv)},
            "previous_shadow.csv": {"path": str(prev_csv), "sha256": sha256_file(prev_csv)},
            "current.csv": {"path": str(curr_csv), "sha256": sha256_file(curr_csv)},
        },
        "results": {},
    }

    for thr in thresholds:
        thr_key = f"{thr:.2f}"
        thr_dir = (out / f"thr_{thr_key}").resolve()
        thr_dir.mkdir(parents=True, exist_ok=True)

        edge_sets: List[set[tuple[str, str]]] = []
        nt_deltas_all: List[float] = []
        marks_counts: List[int] = []

        for i in range(1, k + 1):
            run_dir = thr_dir / f"run_{i:02d}"
            run_dir.mkdir(parents=True, exist_ok=True)

            r_out = run_dir / "riftlens"
            r_out.mkdir(parents=True, exist_ok=True)
            run_cmd(
                [
                    "python",
                    "-m",
                    "riftlens",
                    str(multi_csv),
                    "--corr-threshold",
                    str(thr),
                    "--output-dir",
                    str(r_out),
                ],
                cwd=rift,
                env=env,
            )
            edge_sets.append(edge_set_from_report(r_out / "graph_report.json"))

            nt_prev = run_dir / "nulltrace_prev"
            nt_curr = run_dir / "nulltrace_curr"
            nt_prev.mkdir(parents=True, exist_ok=True)
            nt_curr.mkdir(parents=True, exist_ok=True)

            run_cmd(["python", "-m", "nulltrace", "snapshot", str(prev_csv), "--output-dir", str(nt_prev)], cwd=nt, env=env)
            manifests = sorted(
                (nt_prev / "shadows").glob("*/manifest.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            prev_manifest = manifests[0]
            run_cmd(
                ["python", "-m", "nulltrace", "snapshot", str(curr_csv), "--previous-shadow", str(prev_manifest), "--output-dir", str(nt_curr)],
                cwd=nt,
                env=env,
            )

            diffs = sorted((nt_curr / "shadows").glob("*/shadow_diff.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if diffs:
                nt_deltas_all.extend(extract_nulltrace_abs_deltas(diffs[0]))

            v_out = run_dir / "vault"
            v_out.mkdir(parents=True, exist_ok=True)
            run_cmd(["python", "-m", "voidmark", str(r_out / "graph_report.json"), "--vault-dir", str(v_out)], cwd=vm, env=env)
            marks_counts.append(
                len(list(v_out.rglob("*.json"))) + len(list(v_out.rglob("*.md"))) + len(list(v_out.rglob("*.txt")))
            )

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
