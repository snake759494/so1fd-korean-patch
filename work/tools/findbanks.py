"""Inventory every text bank: a blob whose tail is
   u32 count | u32 12 | u8 widths[count] | u8 bitmaps[count*24]."""
from __future__ import annotations

import json
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load


def bank_font(d: bytes):
    n = len(d)
    for pad in range(0, 4):
        end = n - pad
        for cnt in range(16, 8000):
            base = end - cnt * 24
            hdr = base - cnt - 8
            if hdr < 0:
                break
            if struct.unpack_from("<2I", d, hdr) == (cnt, 12):
                return {"count": cnt, "hdr": hdr, "widths": hdr + 8,
                        "bitmaps": base, "end": end}
    return None


def main():
    rows = []
    for i in range(14320):
        try:
            d = load(i)
        except Exception:
            continue
        if len(d) < 1024:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            if len(blob) < 1024:
                continue
            f = bank_font(blob)
            if f:
                rows.append({"path": p, "len": len(blob), **f})
                print(f"  {p:<20} len={len(blob):<9} glyphs={f['count']:<6} "
                      f"hdr=0x{f['hdr']:X}", flush=True)
        if i % 1000 == 0:
            print("..", i, flush=True)
    json.dump(rows, open(r"D:\psp\rom\SO1\work\banks.json", "w"), indent=1)
    print("banks:", len(rows), "glyph slots", sum(r["count"] for r in rows))


if __name__ == "__main__":
    main()
