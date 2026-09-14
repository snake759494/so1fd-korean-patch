"""Scan every recursively expanded leaf for genuine Japanese Shift-JIS text."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load
from scan_sjis import scan

OUT = r"D:\psp\rom\SO1\work\unpack"


def main():
    manifest = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    rows = []
    for rec in manifest:
        i = rec["idx"]
        d = load(i)
        if not d:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            hits = scan(blob)
            if hits:
                chars = sum(len(t) for _, t in hits)
                if chars >= 12:
                    rows.append({"path": p, "len": len(blob), "runs": len(hits),
                                 "chars": chars, "samples": [t[:40] for _, t in hits[:3]]})
        if i % 2000 == 0:
            print("..", i, flush=True)
    rows.sort(key=lambda r: -r["chars"])
    print("leaves with Japanese:", len(rows))
    for r in rows[:50]:
        print(f"  {r['path']:<20} len={r['len']:<8} runs={r['runs']:<5} chars={r['chars']:<6} "
              + " | ".join(r["samples"]))
    json.dump(rows, open(r"D:\psp\rom\SO1\work\leaf_jp.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
