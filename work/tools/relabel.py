"""Recompute canonical glyph labels from the saved inventory."""
from __future__ import annotations

import json
import pickle
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canon

CAT = r"D:\psp\rom\SO1\work\banks.json"
INV = r"D:\psp\rom\SO1\work\glyphs.pkl"


def main():
    cat = json.load(open(CAT))
    inv = pickle.load(open(INV, "rb"))
    votes: dict[int, Counter] = {}
    for r in cat:
        if not r["path"].endswith("/t1!"):
            continue
        ids = inv["banks"][r["key"]]["ids"]
        for idx, g in enumerate(ids[:272]):
            votes.setdefault(g, Counter())[canon.PREFIX[idx]] += 1
    label = {g: c.most_common(1)[0][0] for g, c in votes.items()}
    inv["canon"] = label
    pickle.dump(inv, open(INV, "wb"))
    print("canonical labels:", len(label), "of", len(inv["glyphs"]), "glyphs")


if __name__ == "__main__":
    main()
