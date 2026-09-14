"""Render text-bank messages with the bank's own 12x12 glyph table."""
from __future__ import annotations

import struct
import sys
import os

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import load


def index_of(d: bytes):
    ents = []
    off = 0
    while off + 4 <= len(d):
        cid, coff = struct.unpack_from("<2H", d, off)
        if cid == 0xFFFF:
            off += 2
            break
        ents.append((cid, coff))
        off += 4
    return ents, off


def codes(d: bytes, off: int, limit=400):
    out = []
    p = off
    while p + 2 <= len(d) and len(out) < limit:
        v = struct.unpack_from("<H", d, p)[0]
        p += 2
        if v == 0:
            break
        out.append(v)
    return out


def draw(d: bytes, bmp_base: int, glyph_idx: int, img, x, y):
    o = bmp_base + glyph_idx * 24
    if o < 0 or o + 24 > len(d):
        return
    px = img.load()
    for r in range(12):
        v = (d[o + r * 2] << 8) | d[o + r * 2 + 1]
        for c in range(12):
            if (v >> (15 - c)) & 1:
                if 0 <= x + c < img.width and 0 <= y + r < img.height:
                    px[x + c, y + r] = 255


def main():
    member = int(sys.argv[1])
    bmp_base = int(sys.argv[2], 0)
    sub = int(sys.argv[3], 0)          # code -> glyph index offset
    out = sys.argv[4] if len(sys.argv) > 4 else "msg.png"
    n = int(sys.argv[5]) if len(sys.argv) > 5 else 40
    d = load(member)
    ents, _ = index_of(d)
    img = Image.new("L", (900, 14 * n), 0)
    for row, (cid, off) in enumerate(ents[:n]):
        cs = codes(d, off)
        x = 0
        for c in cs:
            gi = c - sub
            draw(d, bmp_base, gi, img, x, row * 14)
            x += 12
            if x > 880:
                break
    img.resize((img.width * 2, img.height * 2)).save(out)
    print("->", out, "messages", len(ents))


if __name__ == "__main__":
    main()
