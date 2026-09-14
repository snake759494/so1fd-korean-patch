"""Render a raw blob as a bitmap under a guessed bit depth / row width."""
from __future__ import annotations

import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load


def get_blob(spec: str) -> bytes:
    if "/" in spec or "!" in spec:
        base = spec.split("/")[0].rstrip("!")
        leaves = []
        expand(load(int(base)), base, leaves)
        for p, d in leaves:
            if p == spec:
                return d
        raise KeyError(spec)
    return load(int(spec))


def render(blob: bytes, bpp: int, row_bytes: int, off: int = 0, max_rows: int = 4096):
    data = blob[off:]
    rows = min(len(data) // row_bytes, max_rows)
    w = row_bytes * 8 // bpp
    img = Image.new("L", (w, rows))
    px = img.load()
    for y in range(rows):
        base = y * row_bytes
        x = 0
        for k in range(row_bytes):
            b = data[base + k]
            if bpp == 8:
                px[x, y] = b
                x += 1
            elif bpp == 4:
                px[x, y] = (b & 0x0F) * 17
                px[x + 1, y] = (b >> 4) * 17
                x += 2
            elif bpp == 2:
                for s in (0, 2, 4, 6):
                    px[x, y] = ((b >> s) & 3) * 85
                    x += 1
            elif bpp == 1:
                for s in range(8):
                    px[x, y] = 255 if (b >> s) & 1 else 0
                    x += 1
    return img


if __name__ == "__main__":
    spec = sys.argv[1]
    bpp = int(sys.argv[2])
    row_bytes = int(sys.argv[3], 0)
    off = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0
    out = sys.argv[5] if len(sys.argv) > 5 else "render.png"
    blob = get_blob(spec)
    print(spec, "len", len(blob))
    render(blob, bpp, row_bytes, off).save(out)
    print("->", out)
