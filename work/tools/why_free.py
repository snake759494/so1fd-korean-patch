"""Why did the patcher think one particular glyph slot was free?

Replays the patcher's own reasoning for a single member and glyph index and
prints every reference it found, so a slot that was freed while a reference to
it survived can be traced to the exact byte that was mishandled.
"""
from __future__ import annotations

import json
import pickle
import sys
import os
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
import codemap
import tree
from autopatch import shell_depth, load_rows, KEEP

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"


def main():
    member = int(sys.argv[1])
    want = int(sys.argv[2])
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    label = inv.get("label") or inv["canon"]
    rows = [r for r in load_rows() if int(r["path"].split("/")[0]) == member]
    mode = rows[0]["mode"] if rows else codemap.PAGED
    key, count = inv["member_font"][member]
    fi = cat[key]
    ids = inv["banks"][key]["ids"]

    p = Pack()
    root = tree.parse(p.read(member), str(member))
    p.close()
    k = shell_depth(root)
    pre = str(member)
    fpath = pre + "!" * k + fi["path"][len(pre):]
    leaves = {n.path: n for n in tree.walk(root) if n.data and not n.kids}

    print(f"member {member} glyph {want} = {label.get(ids[want])!r} "
          f"count={count} mode={mode}")
    print(f"font leaf path: {fpath}  (present: {fpath in leaves})")
    total = 0
    for path, node in leaves.items():
        b = node.data
        if len(b) < 2:
            continue
        arr = np.frombuffer(b, dtype=np.uint8).astype(np.int32)
        slot = (arr[:-1] | (arr[1:] << 8)) - 0x101
        idx = slot if mode == codemap.FLAT else slot - 128 * (slot // 256)
        live = (idx >= 0) & (idx < count) & (slot >= 0)
        if path == fpath:
            live[max(0, fi["hdr"] - 1): fi["end"]] = False
        hits = np.flatnonzero(live & (idx == want))
        if hits.size:
            total += hits.size
            print(f"  {path}: {hits.size} refs, first at {hits[:6].tolist()}"
                  f"  slots={[int(slot[h]) for h in hits[:6]]}")
    print(f"total live references to glyph {want}: {total}")


if __name__ == "__main__":
    main()
