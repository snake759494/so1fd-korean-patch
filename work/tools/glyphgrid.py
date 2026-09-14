"""Render a blob as a grid of fixed-size glyph cells."""
from __future__ import annotations

import sys

from PIL import Image


def render(data: bytes, gw: int, gh: int, bpp: int, cols: int, msb: bool = True,
           row_bytes: int = None, cell_bytes: int = None, limit=4000):
    row_bytes = row_bytes or (gw * bpp + 7) // 8
    cell = cell_bytes or row_bytes * gh
    n = min(len(data) // cell, limit)
    rows = (n + cols - 1) // cols
    img = Image.new("L", (cols * (gw + 1), rows * (gh + 1)), 40)
    px = img.load()
    for g in range(n):
        gx = (g % cols) * (gw + 1)
        gy = (g // cols) * (gh + 1)
        base = g * cell
        for y in range(gh):
            ro = base + y * row_bytes
            for x in range(gw):
                if bpp == 1:
                    b = data[ro + x // 8]
                    bit = (b >> (7 - x % 8)) & 1 if msb else (b >> (x % 8)) & 1
                    v = 255 if bit else 0
                elif bpp == 2:
                    b = data[ro + x // 4]
                    sh = (6 - 2 * (x % 4)) if msb else (2 * (x % 4))
                    v = ((b >> sh) & 3) * 85
                else:
                    b = data[ro + x // 2]
                    v = ((b >> 4) if (x % 2 == (0 if msb else 1)) else (b & 15)) * 17
                px[gx + x, gy + y] = v
    return img


if __name__ == "__main__":
    path, off, size = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
    gw, gh, bpp, cols = (int(sys.argv[i]) for i in (4, 5, 6, 7))
    msb = (sys.argv[8] != "lsb") if len(sys.argv) > 8 else True
    out = sys.argv[9] if len(sys.argv) > 9 else "grid.png"
    with open(path, "rb") as f:
        f.seek(off)
        data = f.read(size)
    render(data, gw, gh, bpp, cols, msb).save(out)
    print("->", out)
