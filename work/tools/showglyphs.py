"""Render specific glyph ids side by side, large, with their current labels."""
from __future__ import annotations

import pickle
import sys
import os

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"


def main():
    ids = [int(a) for a in sys.argv[1:]]
    inv = pickle.load(open(INV, "rb"))
    lab = inv.get("label", inv["canon"])
    img = Image.new("L", (len(ids) * 14, 14), 40)
    px = img.load()
    for i, g in enumerate(ids):
        bm = inv["glyphs"][g]
        for r in range(12):
            v = (bm[r * 2] << 8) | bm[r * 2 + 1]
            for c in range(12):
                if (v >> (15 - c)) & 1:
                    px[i * 14 + c + 1, r + 1] = 255
    img.resize((img.width * 14, img.height * 14), Image.NEAREST).save(
        r"D:\psp\rom\SO1\work\show.png")
    print("current:", "".join(lab.get(g, "?") for g in ids))
    print("ids:", ids)


if __name__ == "__main__":
    main()
