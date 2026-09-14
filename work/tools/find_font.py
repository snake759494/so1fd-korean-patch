"""Locate the source glyph bitmaps for a glyph lifted from PPSSPP's glyph cache.

The runtime cache texture has binary alpha, so the font is 1bpp (or 4bpp with
only 0/F).  Build the byte encoding of one known 12x12 glyph under several
plausible layouts and scan every unpacked leaf plus the executable for it.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

CACHE = r"D:\psp\rom\SO1\work\ppsspp\memstick\PSP\TEXTURES\ULJM05290\new\08c2af00736e7efce18f59a0.png"


def glyph_bits(x0, y0, w=12, h=12):
    a = np.array(Image.open(CACHE).convert("RGBA"))
    return (a[y0:y0 + h, x0:x0 + w, 3] > 64).astype(np.uint8)


def enc_1bpp(bits, msb=True, row_bytes=2):
    rows = []
    h, w = bits.shape
    for y in range(h):
        val = 0
        for x in range(w):
            if bits[y, x]:
                val |= (1 << (row_bytes * 8 - 1 - x)) if msb else (1 << x)
        rows.append(val.to_bytes(row_bytes, "big" if msb else "little"))
    return b"".join(rows)


def enc_4bpp(bits, lo_first=True):
    rows = []
    h, w = bits.shape
    for y in range(h):
        row = bytearray()
        for x in range(0, w, 2):
            a = 0x0F if bits[y, x] else 0
            b = 0x0F if bits[y, x + 1] else 0
            row.append((a | (b << 4)) if lo_first else ((a << 4) | b))
        rows.append(bytes(row))
    return b"".join(rows)


def patterns(bits):
    out = {}
    for rb in (2, 3):
        out[f"1bpp_msb_rb{rb}"] = enc_1bpp(bits, True, rb)
        out[f"1bpp_lsb_rb{rb}"] = enc_1bpp(bits, False, rb)
    out["4bpp_lo"] = enc_4bpp(bits, True)
    out["4bpp_hi"] = enc_4bpp(bits, False)
    return out


def search(blob: bytes, pats: dict, rows_needed=8):
    """Look for >= rows_needed consecutive encoded rows anywhere in blob."""
    hits = []
    for name, full in pats.items():
        rb = len(full) // 12
        for start in (0, 2):
            frag = full[start * rb:(start + rows_needed) * rb]
            if len(frag) < rows_needed * rb:
                continue
            p = blob.find(frag)
            if p >= 0:
                hits.append((name, start, p))
                break
    return hits


def main():
    OUT = r"D:\psp\rom\SO1\work\unpack"
    bits = glyph_bits(0, 40)
    print("target glyph:")
    for r in bits:
        print("   " + "".join("#" if v else "." for v in r))
    pats = patterns(bits)
    for k, v in pats.items():
        print(f"  {k}: {v[:8].hex()}... ({len(v)} bytes)")

    targets = [("BOOT.BIN", open(r"D:\psp\rom\SO1\work\extract\PSP_GAME\SYSDIR\BOOT.BIN", "rb").read())]
    for name, blob in targets:
        h = search(blob, pats)
        if h:
            print(name, "HIT", h)

    manifest = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    found = 0
    for rec in manifest:
        i = rec["idx"]
        d = load(i)
        if len(d) < 256:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            h = search(blob, pats)
            if h:
                print("HIT", p, len(blob), h, flush=True)
                found += 1
        if i % 2000 == 0:
            print("..", i, flush=True)
    print("total hits", found)


if __name__ == "__main__":
    main()
