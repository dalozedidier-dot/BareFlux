from pathlib import Path
import json
import subprocess
import sys

def test_cli_run_smoke(tmp_path: Path):
    out = tmp_path / "out"
    cmd = [sys.executable, "-m", "apexobserver.cli", "run", "--input", "examples/minimal_timeseries.csv", "--output", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + "\n" + r.stderr

    assert (out / "batch_manifest.json").exists()
    bm = json.loads((out / "batch_manifest.json").read_text(encoding="utf-8"))
    assert bm["runs"]

    run_dir = out / bm["runs"][0]["run_dir"]
    assert (run_dir / "report.json").exists()
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "hashes.sha256").exists()

def test_invalid_input_generates_report(tmp_path: Path):
    bad = tmp_path / "bad.csv"
    bad.write_text("not,a,csv\n\x00\x00", encoding="utf-8", errors="ignore")
    out = tmp_path / "out"
    cmd = [sys.executable, "-m", "apexobserver.cli", "run", "--input", str(bad), "--output", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0
    bm = json.loads((out / "batch_manifest.json").read_text(encoding="utf-8"))
    run_dir = out / bm["runs"][0]["run_dir"]
    rep = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert rep["status"] in ("invalid_input", "partial", "ok")
