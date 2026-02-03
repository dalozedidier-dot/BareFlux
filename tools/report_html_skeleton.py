#!/usr/bin/env python3
"""Rapport HTML minimal (advanced skeleton).

- Insère des images PNG (hist/boxplot/graph) si présentes.
- Ajoute des liens vers JSON/CSV.

Usage:
  python tools/report_html_skeleton.py --outdir _bareflux_out --html _bareflux_out/report.html
"""
from __future__ import annotations
import argparse, os

TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>BareFlux report</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.card {{ border: 1px solid #ddd; border-radius: 10px; padding: 12px; }}
img {{ max-width: 100%; height: auto; border-radius: 8px; }}
code {{ background: #f6f6f6; padding: 2px 6px; border-radius: 6px; }}
</style>
</head>
<body>
<h1>BareFlux — CI report</h1>
<p>Répertoire: <code>{outdir}</code></p>

<div class="grid">
  <div class="card">
    <h2>Shadow deltas (b)</h2>
    {img_b}
  </div>
  <div class="card">
    <h2>RiftLens graph</h2>
    {img_graph}
  </div>
</div>

<h2>Outputs</h2>
<ul>
  <li><a href="bareflux_ci_status.json">bareflux_ci_status.json</a></li>
  <li><a href="bareflux_column_b_readability.json">bareflux_column_b_readability.json</a></li>
  <li><a href="bareflux_trend.csv">bareflux_trend.csv</a></li>
</ul>

</body>
</html>
"""

def img_tag(path):
    return f'<img src="{path}" alt="{path}"/>' if os.path.exists(path) else "<p>(image absente)</p>"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="_bareflux_out")
    ap.add_argument("--html", default="_bareflux_out/report.html")
    args = ap.parse_args()

    outdir = args.outdir
    img_b = img_tag(os.path.join(outdir, "delta_b_hist.png"))
    img_graph = img_tag(os.path.join(outdir, "riftlens", "coherence_graph.png"))

    html = TEMPLATE.format(outdir=outdir, img_b=img_b, img_graph=img_graph)
    os.makedirs(os.path.dirname(args.html) or ".", exist_ok=True)
    with open(args.html,"w",encoding="utf-8") as f:
        f.write(html)
    print("OK", args.html)

if __name__=="__main__":
    main()
