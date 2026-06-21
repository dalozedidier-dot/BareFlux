from __future__ import annotations

import json
from pathlib import Path
import zipfile

from jsonschema import validate

from bareflux.engine import run_observer
from bareflux.util import load_json_file


def test_run_observer_creates_auditable_bundle(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = repo_root / "tests" / "data" / "minimal_timeseries.csv"
    config = load_json_file(repo_root / "examples" / "bareflux.json")

    out_root = tmp_path / "_bareflux_out"
    run_dir = run_observer(
        input_csv=input_csv,
        output_root=out_root,
        config=config,
        cli_argv=[
            "run",
            "--input",
            str(input_csv),
            "--output",
            str(out_root),
            "--config",
            str(repo_root / "examples" / "bareflux.json"),
        ],
    )

    assert run_dir.exists()
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "hashes.sha256").exists()
    assert (run_dir / "bundle.zip").exists()

    sdir = run_dir / "series" / "minimal"
    for name in ["report.json", "features.csv", "rupture_marks.csv", "errors.json"]:
        assert (sdir / name).exists()

    schemas_dir = repo_root / "src" / "bareflux" / "schemas"
    manifest_schema = json.loads(
        (schemas_dir / "run_manifest.schema.json").read_text(encoding="utf-8")
    )
    report_schema = json.loads(
        (schemas_dir / "report.schema.json").read_text(encoding="utf-8")
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    validate(manifest, manifest_schema)

    report = json.loads((sdir / "report.json").read_text(encoding="utf-8"))
    validate(report, report_schema)

    hashes = (run_dir / "hashes.sha256").read_text(encoding="utf-8")
    assert "bundle.zip" in hashes
    assert "run_manifest.json" in hashes

    with zipfile.ZipFile(run_dir / "bundle.zip", "r") as zf:
        names = set(zf.namelist())
    assert "run_manifest.json" in names
    assert "config_used.json" in names
    assert "inputs/minimal_timeseries.csv" in names
    assert "series/minimal/report.json" in names


def test_bareflux_cli_imports():
    import bareflux.cli  # noqa: F401
