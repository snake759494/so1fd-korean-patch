"""Look for a glyph -> character code table that sits next to a font block.

A font of N glyphs would be accompanied by N codes (Shift-JIS, JIS or Unicode)
if the game keeps one; finding it removes the need to read glyphs by eye.
"""
from __future__ import annotations

import json
import pickle
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

CAT = r"D:\psp\rom\SO1\work\banks.json"


def sjis_ok(v: int) -> bool:
    hi, lo = v >> 8, v & 0xFF
    if 0x20 <= v <= 0x7E:
        return True
    if not (0x81 <= hi <= 0x9F or 0xE0 <= hi <= 0xEF):
        return False
    return 0x40 <= lo <= 0xFC and lo != 0x7F


def jis_ok(v: int) -> bool:
    hi, lo = v >> 8, v & 0xFF
    return 0x21 <= hi <= 0x74 and 0x21 <= lo <= 0x7E


def uni_ok(v: int) -> bool:
    return (0x20 <= v <= 0x7E or 0x3000 <= v <= 0x30FF or
            0x4E00 <= v <= 0x9FFF or 0xFF01 <= v <= 0xFF9F)


TESTS = [("sjis_le", "<u2", sjis_ok), ("sjis_be", ">u2", sjis_ok),
         ("jis_le", "<u2", jis_ok), ("jis_be", ">u2", jis_ok),
         ("uni_le", "<u2", uni_ok), ("uni_be", ">u2", uni_ok)]


def scan(blob: bytes, count: int, label=""):
    hits = []
    n = len(blob)
    for name, dt, ok in TESTS:
        for phase in (0, 1):
            m = (n - phase) // 2
            if m < count:
                continue
            u = np.frombuffer(blob, dtype=dt, count=m, offset=phase)
            good = np.fromiter((ok(int(x)) for x in u), dtype=bool, count=m)
            # longest window of `count` all-good values
            c = np.concatenate(([0], np.cumsum(good)))
            win = c[count:] - c[:-count]
            best = int(win.max()) if win.size else 0
            if best == count:
                for p in np.flatnonzero(win == count)[:3]:
                    hits.append((name, phase + int(p) * 2, count))
    return hits


def main():
    cat = json.load(open(CAT))
    targets = [int(a) for a in sys.argv[1:]] or [2351]
    for m in targets:
        rows = [r for r in cat if r["member"] == m]
        if not rows:
            print(m, "no font")
            continue
        leaves = []
        expand(load(m), str(m), leaves)
        for r in rows:
            print(f"member {m} font {r['key']} count={r['count']}")
            for p, blob in leaves:
                for name, off, cnt in scan(blob, r["count"]):
                    print(f"   candidate table in {p} @0x{off:X} as {name}")


if __name__ == "__main__":
    main()
