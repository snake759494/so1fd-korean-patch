"""Overwrite glyph labels for one 'top glyphs' page with a corrected reading."""
from __future__ import annotations

import json
import pickle
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
TOP = r"D:\psp\rom\SO1\work\top"


def main():
    start = int(sys.argv[1])
    text = sys.argv[2]
    sel = json.load(open(os.path.join(TOP, f"top{start:04d}.json")))
    if len(text) != len(sel):
        print(f"length mismatch: {len(text)} chars vs {len(sel)} glyphs")
        return 1
    inv = pickle.load(open(INV, "rb"))
    manual = inv["manual"]
    changed = 0
    for g, ch in zip(sel, text):
        if manual.get(g) != ch:
            changed += 1
        manual[g] = ch
    inv["manual"] = manual
    label = dict(inv["canon"])
    label.update(manual)
    inv["label"] = label
    pickle.dump(inv, open(INV, "wb"))
    print(f"page {start}: {changed} labels corrected; total {len(label)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
