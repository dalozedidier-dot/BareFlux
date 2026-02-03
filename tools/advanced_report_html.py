#!/usr/bin/env python3
"""
Advanced (optional): génère un mini rapport HTML (sans dépendances lourdes).
- Inclut liens vers JSON/CSV produits par postprocess.
- Si des PNG existent, ils seront référencés.

Usage:
  python tools/advanced_report_html.py --out _bareflux_out --html _bareflux_out/report.html
"""
from __future__ import annotations

import argparse
import glob
import html as _html
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_bareflux_out")
    ap.add_argument("--html", default="_bareflux_out/report.html")
    args = ap.parse_args()

    out_dir = args.out
    items = []
    for pat in ["*.json", "*.csv", "*.png"]:
        items += glob.glob(os.path.join(out_dir, pat))
    items.sort()

    lines = []
    lines.append("<html><head><meta charset='utf-8'><title>BareFlux Report</title></head><body>")
    lines.append("<h1>BareFlux Report</h1>")
    lines.append("<p>Fichiers générés:</p><ul>")
    for fp in items:
        name = os.path.basename(fp)
        lines.append(f"<li><a href='{_html.escape(name)}'>{_html.escape(name)}</a></li>")
    lines.append("</ul>")
    lines.append("</body></html>")

    os.makedirs(os.path.dirname(args.html), exist_ok=True)
    with open(args.html, "w", encoding="utf-8") as f:
        f.write("
".join(lines))
    print("OK", args.html)


if __name__ == "__main__":
    main()
