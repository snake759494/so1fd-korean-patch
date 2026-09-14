"""Rebuild the bank catalogue and the unique-glyph inventory with the fixed
font locator, and label every glyph that lies in the canonical prefix."""
from __future__ import annotations

import json
import pickle
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load
from fieldbank import font
import canon

CAT = r"D:\psp\rom\SO1\work\banks.json"
INV = r"D:\psp\rom\SO1\work\glyphs.pkl"


def main():
    cat = []
    uniq: dict[bytes, int] = {}
    order: list[bytes] = []
    per_bank = {}
    for i in range(14320):
        try:
            d = load(i)
        except Exception:
            continue
        if len(d) < 1024:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            if len(blob) < 1024:
                continue
            f = font(blob)
            if not f:
                continue
            cat.append({"path": p, "member": i, "len": len(blob), **f})
            b, n = f["bitmaps"], f["count"]
            ids = []
            for g in range(n):
                bm = blob[b + g * 24: b + g * 24 + 24]
                k = uniq.get(bm)
                if k is None:
                    k = len(order)
                    uniq[bm] = k
                    order.append(bm)
                ids.append(k)
            per_bank[p] = {"ids": ids,
                           "widths": list(blob[f["widths"]:f["widths"] + n])}
        if i % 2000 == 0:
            print("..", i, flush=True)

    # canonical labels: a glyph seen at index < 272 in any bank gets that char
    label: dict[int, str] = {}
    votes: dict[int, Counter] = {}
    for p, v in per_bank.items():
        for idx, g in enumerate(v["ids"][:272]):
            votes.setdefault(g, Counter())[canon.PREFIX[idx]] += 1
    for g, c in votes.items():
        label[g] = c.most_common(1)[0][0]
    conflicts = sum(1 for c in votes.values() if len(c) > 1)

    json.dump(cat, open(CAT, "w"), indent=1)
    pickle.dump({"glyphs": order, "banks": per_bank, "canon": label},
                open(INV, "wb"))
    print("banks", len(cat), "unique glyphs", len(order),
          "canonical-labelled", len(label), "conflicting", conflicts)
    print("unlabelled glyphs:", len(order) - len(label))


if __name__ == "__main__":
    main()
