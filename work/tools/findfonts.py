"""Find every 12x12 1bpp glyph table in the game data.

A row is two bytes with only the top 12 bits used, so the low nibble of every
odd byte is zero.  Long runs of that property mark glyph arrays.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load


def runs(blob: bytes, min_glyphs=64):
    a = np.frombuffer(blob, dtype=np.uint8)
    out = []
    for phase in (0, 1):
        odd = a[phase + 1::2]
        ok = (odd & 0x0F) == 0
        # find maximal runs of True
        idx = np.flatnonzero(np.diff(np.concatenate(([0], ok.view(np.int8), [0]))))
        for s, e in zip(idx[0::2], idx[1::2]):
            n_rows = e - s
            if n_rows >= min_glyphs * 12:
                start = phase + s * 2
                out.append((start, n_rows // 12, n_rows))
    return out


def main():
    results = []
    for i in range(14320):
        try:
            d = load(i)
        except Exception:
            continue
        if len(d) < 4096:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            if len(blob) < 4096:
                continue
            for start, ng, nr in runs(blob):
                results.append({"path": p, "len": len(blob), "start": start,
                                "glyphs": ng, "rows": nr})
                print(f"  {p:<20} len={len(blob):<8} start=0x{start:X} glyphs~{ng}", flush=True)
        if i % 1000 == 0:
            print("..", i, flush=True)
    json.dump(results, open(r"D:\psp\rom\SO1\work\fonts_found.json", "w"), indent=1)
    print("total", len(results))


if __name__ == "__main__":
    main()
