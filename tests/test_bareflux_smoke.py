from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap


def make_fake_module(modules: Path, name: str, package: str, body: str) -> None:
    pkg = modules / name / "src" / package
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__main__.py").write_text(textwrap.dedent(body), encoding="utf-8")


def make_fake_modules(modules: Path) -> None:
    make_fake_module(
        modules,
        "RiftLens",
        "riftlens",
        """
        import argparse, json
        from pathlib import Path

        p = argparse.ArgumentParser()
        p.add_argument('csv')
        p.add_argument('--corr-threshold', default='0.6')
        p.add_argument('--output-dir', required=True)
        args = p.parse_args()
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / 'graph_report.json').write_text(json.dumps({
            'edges': [{'source': 'x', 'target': 'y', 'weight': 0.9}],
            'threshold': float(args.corr_threshold),
        }), encoding='utf-8')
        """,
    )
    make_fake_module(
        modules,
        "NullTrace",
        "nulltrace",
        """
        import argparse, json, uuid
        from pathlib import Path

        p = argparse.ArgumentParser()
        sub = p.add_subparsers(dest='cmd', required=True)
        snap = sub.add_parser('snapshot')
        snap.add_argument('csv')
        snap.add_argument('--previous-shadow')
        snap.add_argument('--output-dir', required=True)
        args = p.parse_args()
        shadow = Path(args.output_dir) / 'shadows' / uuid.uuid4().hex[:8]
        shadow.mkdir(parents=True, exist_ok=True)
        (shadow / 'manifest.json').write_text(json.dumps({'input': args.csv}), encoding='utf-8')
        if args.previous_shadow:
            (shadow / 'shadow_diff.json').write_text(json.dumps({'diff': {'column_changes': {}}}), encoding='utf-8')
        """,
    )
    make_fake_module(
        modules,
        "VoidMark",
        "voidmark",
        """
        import argparse, json
        from pathlib import Path

        p = argparse.ArgumentParser()
        p.add_argument('graph_report')
        p.add_argument('--vault-dir', required=True)
        args = p.parse_args()
        vault = Path(args.vault_dir)
        vault.mkdir(parents=True, exist_ok=True)
        (vault / 'voidmark_record.json').write_text(json.dumps({'source': args.graph_report}), encoding='utf-8')
        """,
    )


def test_run_modules_strict_with_fake_modules(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    modules = tmp_path / "modules"
    make_fake_modules(modules)

    out = tmp_path / "out"
    cmd = [
        "bash",
        str(repo_root / "run_modules.sh"),
        "--modules-dir",
        str(modules),
        "--out",
        str(out),
        "--strict",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + "\n" + r.stderr

    manifest_path = out / "bareflux_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "PASS"
    assert manifest["strict_errors"] == []
    assert manifest["outputs"]["voidmark"]["vault_file_count"] == 1


def test_robustness_stress_report_is_generated(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    out = tmp_path / "robustness"
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "robustness_stress_tests.py"),
        "--out-dir",
        str(out),
        "--n",
        "80",
        "--seed",
        "12",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + "\n" + r.stderr
    report = json.loads(
        (out / "robustness_stress_report.json").read_text(encoding="utf-8")
    )
    assert report["scenario_count"] >= 6
    assert (out / "strong_shift" / "multi.csv").exists()
