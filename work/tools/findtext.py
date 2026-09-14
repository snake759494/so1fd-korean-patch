"""Locate glyph-coded text: runs of u16 codes in [0x101, 0x101+limit)."""
from __future__ import annotations

import json
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

LO = 0x101
HI = 0x101 + 900
MINRUN = 12


def runs(blob: bytes):
    total = 0
    count = 0
    best = 0
    for phase in (0, 1):
        n = (len(blob) - phase) // 2
        if n < MINRUN:
            continue
        u = np.frombuffer(blob, dtype="<u2", count=n, offset=phase)
        good = (u >= LO) & (u < HI)
        d = np.diff(np.concatenate(([0], good.view(np.int8), [0])))
        idx = np.flatnonzero(d)
        for s, e in zip(idx[0::2], idx[1::2]):
            if e - s >= MINRUN:
                total += e - s
                count += 1
                best = max(best, e - s)
    return count, total, best


def main():
    rows = []
    for i in range(14320):
        try:
            d = load(i)
        except Exception:
            continue
        if len(d) < 128:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            if len(blob) < 128:
                continue
            c, t, b = runs(blob)
            if t >= 300:
                rows.append({"path": p, "len": len(blob), "runs": c, "chars": t, "longest": b})
        if i % 1000 == 0:
            print("..", i, flush=True)
    rows.sort(key=lambda r: -r["chars"])
    print("blobs with text:", len(rows), "total chars", sum(r["chars"] for r in rows))
    for r in rows[:50]:
        print(f"  {r['path']:<18} len={r['len']:<9} runs={r['runs']:<6} chars={r['chars']:<7} longest={r['longest']}")
    json.dump(rows, open(r"D:\psp\rom\SO1\work\text_blobs.json", "w"), indent=1)


if __name__ == "__main__":
    main()
