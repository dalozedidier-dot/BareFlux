from __future__ import annotations
import argparse
import glob
import json
from pathlib import Path
from typing import List, Optional

from .runner import run_batch
from .schema import validate_config

def _expand_inputs(pattern: str) -> List[Path]:
    p = Path(pattern)
    if p.exists() and p.is_dir():
        return sorted([x for x in p.glob("*.csv") if x.is_file()])
    if p.exists() and p.is_file():
        return [p]
    return sorted([Path(x) for x in glob.glob(pattern)])

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="apex", description="ApexObserver: observation descriptive auditable.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    runp = sub.add_parser("run", help="Analyser un ou plusieurs CSV.")
    runp.add_argument("--input", required=True, help="Fichier CSV, dossier, ou glob (ex: examples/*.csv).")
    runp.add_argument("--output", required=True, help="Dossier de sortie (batch).")
    runp.add_argument("--config", default="configs/apex_default.json", help="Config JSON.")
    args = ap.parse_args(argv)

    if args.cmd == "run":
        inputs = _expand_inputs(args.input)
        if not inputs:
            print(f"Aucun CSV trouvé pour: {args.input}")
            return 2

        cfg_path = Path(args.config)
        if not cfg_path.exists():
            print(f"Config introuvable: {cfg_path}")
            return 2

        config_schema = Path("schema/config.schema.json")
        report_schema = Path("schema/report.schema.json")

        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        validate_config(cfg, config_schema)

        out_dir = Path(args.output)
        run_batch(inputs, out_dir, cfg, report_schema)
        return 0

    return 2
