import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .engine import run_observer
from .util import load_json_file


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="apexobserver", description="ApexObserver CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    runp = sub.add_parser("run", help="Run observer on a CSV input")
    runp.add_argument("--input", required=True, help="Path to input CSV")
    runp.add_argument("--output", required=True, help="Output directory (run_* will be created inside)")
    runp.add_argument("--config", required=False, default=None, help="Path to JSON config (optional)")

    schemap = sub.add_parser("schemas", help="Print available JSON schema paths")
    schemap.add_argument("--json", action="store_true", help="Output as JSON")

    return p


def cmd_schemas(as_json: bool) -> int:
    here = Path(__file__).resolve().parent
    schemas = sorted((here / "schemas").glob("*.schema.json"))
    if as_json:
        print(json.dumps([str(p) for p in schemas], indent=2))
    else:
        for p in schemas:
            print(p)
    return 0


def main(argv=None) -> int:
    p = build_parser()
    args = p.parse_args(argv)

    if args.cmd == "schemas":
        return cmd_schemas(args.json)

    if args.cmd == "run":
        output_root = Path(args.output)
        output_root.mkdir(parents=True, exist_ok=True)

        if args.config:
            config = load_json_file(Path(args.config))
        else:
            config = {}

        run_dir = run_observer(
            input_csv=Path(args.input),
            output_root=output_root,
            config=config,
            cli_argv=argv,
        )

        # Minimal run-level report.json for compatibility with smoke tests
        # (keeps detailed per-series report in series/<name>/report.json)
        status = "ok"
        series_reports = []
        try:
            series_dir = run_dir / "series"
            for s in sorted(series_dir.iterdir()):
                rep_path = s / "report.json"
                if rep_path.exists():
                    rep = json.loads(rep_path.read_text(encoding="utf-8"))
                    series_reports.append({"series": s.name, "status": rep.get("status", "")})
                    if rep.get("status") not in ("ok", ""):
                        status = rep.get("status", status)
        except Exception:
            status = status

        run_report = {
            "schema_version": "apexobserver.run_report.v1",
            "run_dir": run_dir.name,
            "status": status,
            "series": series_reports,
        }
        (run_dir / "report.json").write_text(json.dumps(run_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        # Minimal batch_manifest.json at output root
        batch = {
            "schema_version": "apexobserver.batch.v1",
            "utc_created": datetime.now(timezone.utc).isoformat(),
            "runs": [{"run_dir": run_dir.name, "status": status}],
        }
        (output_root / "batch_manifest.json").write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0

    p.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

