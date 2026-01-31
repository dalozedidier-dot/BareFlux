import argparse
import json
from pathlib import Path

from .engine import run_observer
from .util import load_json_file


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="apexobserver", description="ApexObserver CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    runp = sub.add_parser("run", help="Run observer on a CSV input")
    runp.add_argument("--input", required=True, help="Path to input CSV")
    runp.add_argument("--output", required=True, help="Output directory (run_* will be created inside)")
    runp.add_argument("--config", required=True, help="Path to JSON config")

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
        config = load_json_file(Path(args.config))
        run_observer(
            input_csv=Path(args.input),
            output_root=Path(args.output),
            config=config,
            cli_argv=argv,
        )
        return 0

    p.error("Unknown command")
    return 2
