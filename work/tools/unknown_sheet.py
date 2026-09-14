"""Render the unlabelled glyphs, most-used first, as readable grids."""
from __future__ import annotations

import json
import pickle
import sys
import os

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
UNK = r"D:\psp\rom\SO1\work\unknown_glyphs.json"
COLS = 12
ROWS = 10
SCALE = 7


def main():
    inv = pickle.load(open(INV, "rb"))
    unk = json.load(open(UNK))
    ids = [int(k) for k in unk]
    counts = [unk[k] for k in unk]
    tot = sum(counts)
    acc = 0
    for i, c in enumerate(counts):
        acc += c
        if acc >= tot * 0.99:
            print(f"top {i + 1} glyphs cover 99% of unknown uses")
            break
    per = COLS * ROWS
    order = []
    for page in range((len(ids) + per - 1) // per):
        sel = ids[page * per:(page + 1) * per]
        img = Image.new("L", (COLS * 14, ROWS * 14), 40)
        px = img.load()
        for i, g in enumerate(sel):
            bm = inv["glyphs"][g]
            ox, oy = (i % COLS) * 14, (i // COLS) * 14
            for r in range(12):
                v = (bm[r * 2] << 8) | bm[r * 2 + 1]
                for c in range(12):
                    if (v >> (15 - c)) & 1:
                        px[ox + c + 1, oy + r + 1] = 255
        img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST).save(
            rf"D:\psp\rom\SO1\work\unk\page{page:02d}.png")
        order.append(sel)
    json.dump(order, open(r"D:\psp\rom\SO1\work\unk\order.json", "w"))
    print("pages:", len(order), "glyphs:", len(ids))


if __name__ == "__main__":
    os.makedirs(r"D:\psp\rom\SO1\work\unk", exist_ok=True)
    main()
