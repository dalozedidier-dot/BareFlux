from __future__ import annotations

import argparse
from bareflux.orchestration import main as orchestration_main


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build BareFlux mass-collect overview."
    )
    parser.add_argument("--mass-dir", default="_ci_out/mass")
    parser.add_argument("--out-json", default="_ci_out/mass/mass_collect_overview.json")
    parser.add_argument("--out-csv", default="_ci_out/mass/mass_collect_summary.csv")
    args = parser.parse_args()
    return orchestration_main(
        [
            "mass-overview",
            "--mass-dir",
            args.mass_dir,
            "--out-json",
            args.out_json,
            "--out-csv",
            args.out_csv,
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
