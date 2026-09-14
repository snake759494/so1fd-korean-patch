"""Bounds check for every font block we write into.

Writing a glyph touches widths[gi] and bitmaps[gi*24 .. +24).  If the detected
glyph count over-runs the real array, those writes land on whatever follows the
font - which is exactly the kind of damage that boots fine until the screen
that uses it.  This proves, per bank, that the whole written range stays inside
the font block and inside the leaf.
"""
from __future__ import annotations

import json
import pickle
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
import tree
from autopatch import shell_depth

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"
BUILD = r"D:\psp\rom\SO1\work\build"


def main():
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    ov = pickle.load(open(os.path.join(BUILD, "overrides.pkl"), "rb"))
    pack = Pack()
    bad = Counter()
    examples = []
    for m in sorted(ov):
        key, count = inv["member_font"][m]
        fi = cat[key]
        root = tree.parse(pack.read(m), str(m))
        k = shell_depth(root)
        pre = str(m)
        leaves = {}
        for n in tree.walk(root):
            p = n.path
            if p.startswith(pre + "!" * k):
                p = pre + p[len(pre) + k:]
            leaves[p] = n
        node = leaves.get(fi["path"])
        if node is None or node.data is None:
            bad["no_leaf"] += 1
            continue
        L = len(node.data)
        w0, w1 = fi["widths"], fi["widths"] + count
        b0, b1 = fi["bitmaps"], fi["bitmaps"] + count * 24
        probs = []
        if b1 > L:
            probs.append(f"bitmaps end {b1} > leaf {L}")
        if b1 > fi["end"]:
            probs.append(f"bitmaps end {b1} > block end {fi['end']}")
        if w1 > b0:
            probs.append(f"widths end {w1} > bitmaps {b0}")
        if fi["widths"] < fi["hdr"] + 7:
            probs.append(f"widths {fi['widths']} before hdr+7 {fi['hdr'] + 7}")
        if count != fi["count"]:
            probs.append(f"count {count} != catalogue {fi['count']}")
        if probs:
            bad["bad"] += 1
            if len(examples) < 15:
                examples.append((m, fi["path"], probs))
        else:
            bad["ok"] += 1
    pack.close()
    print(dict(bad))
    for m, path, probs in examples:
        print(f"  member {m} {path}: " + "; ".join(probs))


if __name__ == "__main__":
    main()
