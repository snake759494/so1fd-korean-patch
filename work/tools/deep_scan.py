"""Brute-force sweep: decode every SLZ container found at any offset in any
member (recursively) and look for genuine Shift-JIS Japanese text."""
from __future__ import annotations

import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slz
from expand import load
from scan_sjis import scan

OUT = r"D:\psp\rom\SO1\work\unpack"


def slz_positions(d: bytes):
    """Every offset where a plausible SLZ container header starts."""
    out = []
    p = d.find(b"SLZ")
    while p >= 0:
        if p + 16 <= len(d) and d[p + 3] in (0, 1, 2, 3):
            comp, unp, _nxt = struct.unpack_from("<3I", d, p + 4)
            if 0 < comp <= len(d) - p - 16 + 64 and 0 < unp < 64 << 20:
                out.append(p)
        p = d.find(b"SLZ", p + 1)
    return out


def sweep(d: bytes, path: str, out: list, depth=0):
    if depth > 4:
        return
    hits = scan(d)
    if hits and sum(len(t) for _, t in hits) >= 20:
        out.append((path, len(d), len(hits), [t[:44] for _, t in hits[:3]]))
    for p in slz_positions(d):
        try:
            dec = slz.decompress(d[p:])
        except Exception:
            continue
        if len(dec) < 8:
            continue
        sweep(dec, f"{path}@{p:X}!", out, depth + 1)


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 14320
    results = []
    for i in range(lo, hi):
        try:
            d = load(i)
        except Exception:
            continue
        if not d:
            continue
        out = []
        try:
            sweep(d, str(i), out)
        except Exception as e:
            print("err", i, e)
        for r in out:
            print(f"  {r[0]:<26} len={r[1]:<9} runs={r[2]:<5} " + " | ".join(r[3]), flush=True)
        results.extend(out)
        if i % 500 == 0:
            print("..", i, flush=True)
    print("total", len(results))


if __name__ == "__main__":
    main()
