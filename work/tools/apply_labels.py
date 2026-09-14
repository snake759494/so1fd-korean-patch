"""Merge the hand-read glyph labels into the inventory."""
from __future__ import annotations

import io
import json
import pickle
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
ORDER = r"D:\psp\rom\SO1\work\unk\order.json"
LAB = r"D:\psp\rom\SO1\work\unk\labels.txt"


def main():
    inv = pickle.load(open(INV, "rb"))
    order = json.load(open(ORDER))
    pages = [l.strip() for l in io.open(LAB, encoding="utf-8") if l.strip()]
    manual = inv.get("manual", {})
    added = bad = 0
    for pi, chars in enumerate(pages):
        ids = order[pi]
        if len(chars) != len(ids):
            print(f"page {pi}: {len(chars)} labels vs {len(ids)} glyphs -- skipped")
            bad += 1
            continue
        for g, ch in zip(ids, chars):
            manual[g] = ch
            added += 1
    inv["manual"] = manual
    label = dict(inv["canon"])
    label.update(manual)
    inv["label"] = label
    pickle.dump(inv, open(INV, "wb"))
    print(f"manual labels {added} (pages skipped: {bad}); total labelled "
          f"{len(label)} / {len(inv['glyphs'])}")


if __name__ == "__main__":
    main()
