#!/usr/bin/env python3
"""
RiftLens stability: Jaccard similarity nodes/edges entre 2 graph_report.json.
Usage:
  python tools/riftlens_stability.py --g1 prev.json --g2 curr.json --out stability.json
"""
from __future__ import annotations

import argparse
import json


def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def as_edge_set(edges):
    s = set()
    for e in edges or []:
        if isinstance(e, dict):
            u = e.get("source", e.get("u", e.get("a", "")))
            v = e.get("target", e.get("v", e.get("b", "")))
        elif isinstance(e, (list, tuple)) and len(e) >= 2:
            u, v = e[0], e[1]
        else:
            continue
        s.add((str(u), str(v)))
    return s


def jaccard(a, b):
    if not a and not b:
        return 1.0
    inter = len(a & b)
    uni = len(a | b)
    return inter / uni if uni else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g1", required=True)
    ap.add_argument("--g2", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    g1 = load_json(args.g1)
    g2 = load_json(args.g2)

    n1 = set(map(str, g1.get("nodes", [])))
    n2 = set(map(str, g2.get("nodes", [])))
    e1 = as_edge_set(g1.get("edges", []))
    e2 = as_edge_set(g2.get("edges", []))

    rep = {
        "nodes_jaccard": jaccard(n1, n2),
        "edges_jaccard": jaccard(e1, e2),
        "n_nodes_1": len(n1),
        "n_nodes_2": len(n2),
        "n_edges_1": len(e1),
        "n_edges_2": len(e2),
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)

    print("OK", args.out)


if __name__ == "__main__":
    main()
