"""Render the most-used manually-labelled glyphs, big, for a careful re-read."""
from __future__ import annotations

import collections
import io
import json
import pickle
import sys
import os

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
TSV = r"D:\psp\rom\SO1\work\text.tsv"
OUTDIR = r"D:\psp\rom\SO1\work\top"


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    inv = pickle.load(open(INV, "rb"))
    manual = inv["manual"]
    # usage frequency of each manual glyph, from the decoded text
    freq = collections.Counter()
    lab2g = {}
    for g, ch in manual.items():
        lab2g.setdefault(ch, []).append(g)
    counts = collections.Counter()
    with io.open(TSV, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 6 and not p[0].startswith("5053"):
                counts.update(p[5])
    for g, ch in manual.items():
        freq[g] = counts.get(ch, 0)
    order = [g for g, _ in freq.most_common()]
    sel = order[start:start + n]
    cols = 10
    rows = (len(sel) + cols - 1) // cols
    img = Image.new("L", (cols * 14, rows * 14), 40)
    px = img.load()
    for i, g in enumerate(sel):
        bm = inv["glyphs"][g]
        ox, oy = (i % cols) * 14, (i // cols) * 14
        for r in range(12):
            v = (bm[r * 2] << 8) | bm[r * 2 + 1]
            for c in range(12):
                if (v >> (15 - c)) & 1:
                    px[ox + c + 1, oy + r + 1] = 255
    os.makedirs(OUTDIR, exist_ok=True)
    img.resize((img.width * 11, img.height * 11), Image.NEAREST).save(
        os.path.join(OUTDIR, f"top{start:04d}.png"))
    json.dump(sel, open(os.path.join(OUTDIR, f"top{start:04d}.json"), "w"))
    for r in range(rows):
        print("".join(manual[g] for g in sel[r * cols:(r + 1) * cols]))


if __name__ == "__main__":
    main()
