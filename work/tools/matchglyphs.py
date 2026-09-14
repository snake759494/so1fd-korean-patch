"""Match glyphs rendered on screen against the game's 12x12 glyph tables.

PPSSPP dumped the title-menu strings as textures; the glyphs there are exactly
the font bitmaps, so locating them inside a bank's glyph array gives the glyph
indices of a string whose text we already know.
"""
from __future__ import annotations

import sys
import os

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import load

TEX = r"D:\psp\rom\SO1\work\ppsspp\memstick\PSP\TEXTURES\ULJM05290\new"


def tex_bits(name):
    a = np.array(Image.open(os.path.join(TEX, name)).convert("RGBA"))
    return (a[:, :, 3] > 64).astype(np.uint8)


def bank_glyphs(member: int, base: int, count: int):
    d = load(member)
    out = np.zeros((count, 12, 12), dtype=np.uint8)
    for g in range(count):
        o = base + g * 24
        for r in range(12):
            v = (d[o + r * 2] << 8) | d[o + r * 2 + 1]
            for c in range(12):
                out[g, r, c] = (v >> (15 - c)) & 1
    return out


def main():
    name = sys.argv[1]
    member = int(sys.argv[2])
    base = int(sys.argv[3], 0)
    count = int(sys.argv[4])
    y0 = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    bits = tex_bits(name)
    print("texture", bits.shape, "ink rows",
          [i for i in range(bits.shape[0]) if bits[i].any()])
    glyphs = bank_glyphs(member, base, count)
    # slide a 12x12 window across the texture row and find exact matches
    H, W = bits.shape
    x = 0
    while x + 12 <= W:
        win = bits[y0:y0 + 12, x:x + 12]
        if win.sum() == 0:
            x += 1
            continue
        eq = (glyphs == win).all(axis=(1, 2))
        hits = np.flatnonzero(eq)
        if hits.size:
            print(f"  x={x:3d} -> glyph {hits.tolist()[:5]}  (code {[hex(h + 0x20) for h in hits[:3]]})")
            x += 12
        else:
            x += 1


if __name__ == "__main__":
    main()
