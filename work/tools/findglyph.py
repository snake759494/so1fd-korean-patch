"""Encode glyphs lifted from a dumped texture as 24-byte bitmaps and find them
verbatim in the game data."""
from __future__ import annotations

import sys
import os

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

TEX = r"D:\psp\rom\SO1\work\ppsspp\memstick\PSP\TEXTURES\ULJM05290\new"


def tex_bits(name):
    a = np.array(Image.open(os.path.join(TEX, name)).convert("RGBA"))
    return (a[:, :, 3] > 64).astype(np.uint8)


def encode(win):
    out = bytearray()
    for r in range(12):
        v = 0
        for c in range(12):
            if win[r, c]:
                v |= 1 << (15 - c)
        out += bytes((v >> 8, v & 0xFF))
    return bytes(out)


def targets(name, y0, xs):
    bits = tex_bits(name)
    return [(x, encode(bits[y0:y0 + 12, x:x + 12])) for x in xs]


def main():
    name = sys.argv[1]
    y0 = int(sys.argv[2])
    xs = [int(v) for v in sys.argv[3].split(",")]
    tg = targets(name, y0, xs)
    for x, b in tg:
        print(f"  x={x}: {b.hex()}")
    ram = r"D:\psp\rom\SO1\work\psp_ram.bin"
    if os.path.exists(ram):
        blob = open(ram, "rb").read()
        for x, b in tg:
            p = blob.find(b)
            while p >= 0:
                print(f"RAM x={x} at 0x{p:X} (psp 0x{0x08800000 + p:X})", flush=True)
                p = blob.find(b, p + 1)
    for i in range(14320):
        try:
            d = load(i)
        except Exception:
            continue
        if len(d) < 64:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for path, blob in leaves:
            for x, b in tg:
                p = blob.find(b)
                if p >= 0:
                    print(f"HIT {path} x={x} at 0x{p:X}", flush=True)


if __name__ == "__main__":
    main()
