"""How many glyph slots in a bank are genuinely usable?

Splits the population three ways so the reference scan's false-positive rate
is visible: blank slots, blank slots that nothing references, and blank slots
that survive a stricter validity test (a code must round-trip through the
paged mapping to be a real glyph reference).
"""
from __future__ import annotations

import collections
import json
import pickle
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
import codemap
import tree
from autopatch import shell_depth, load_rows

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"


def main():
    member = int(sys.argv[1]) if len(sys.argv) > 1 else 1709
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    rows = [r for r in load_rows() if int(r["path"].split("/")[0]) == member]
    mode = rows[0]["mode"] if rows else codemap.PAGED
    key, count = inv["member_font"][member]
    fi = cat[key]

    p = Pack()
    root = tree.parse(p.read(member), str(member))
    p.close()
    k = shell_depth(root)
    pre = str(member)
    leaves = {}
    for n in tree.walk(root):
        q = n.path
        if q.startswith(pre + "!" * k):
            q = pre + q[len(pre) + k:]
        leaves[q] = n

    fnode = leaves[fi["path"]]
    bm = fi["bitmaps"]
    blank = {g for g in range(count)
             if not any(fnode.data[bm + g * 24: bm + g * 24 + 24])}

    loose = set()
    strict = set()
    for path, node in leaves.items():
        b = node.data
        if not b or len(b) < 2:
            continue
        arr = np.frombuffer(b, dtype=np.uint8).astype(np.int32)
        slot = (arr[:-1] | (arr[1:] << 8)) - 0x101
        idx = slot if mode == codemap.FLAT else slot - 128 * (slot // 256)
        ok = (slot >= 0) & (idx >= 0) & (idx < count)
        if path == fi["path"]:
            ok[max(0, fi["hdr"] - 1): fi["end"]] = False
        loose.update(np.unique(idx[ok]).tolist())
        # a real reference must round-trip: index -> slot -> index
        back = idx + 128 * np.maximum(0, idx // 128 - 1)
        rt = ok & (back == slot)
        strict.update(np.unique(idx[rt]).tolist())

    print(f"member {member}  bank {key}  count={count}  mode={mode}")
    print(f"  blank slots                        : {len(blank)}")
    print(f"  referenced (loose scan)            : {len(loose)}")
    print(f"  referenced (round-trip validated)  : {len(strict)}")
    print(f"  blank AND unreferenced (loose)     : {len(blank - loose)}")
    print(f"  blank AND unreferenced (strict)    : {len(blank - strict)}")


if __name__ == "__main__":
    main()
