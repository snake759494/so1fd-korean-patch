"""Build the global inventory of unique 12x12 glyph bitmaps used by the banks."""
from __future__ import annotations

import json
import os
import pickle
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

BANKS = r"D:\psp\rom\SO1\work\banks.json"
OUT = r"D:\psp\rom\SO1\work\glyphs.pkl"


def bank_blobs():
    """Yield (path, blob, font_info) for every catalogued bank."""
    rows = json.load(open(BANKS))
    by_member: dict[int, list] = {}
    for r in rows:
        by_member.setdefault(int(r["path"].split("/")[0]), []).append(r)
    for m, rs in sorted(by_member.items()):
        leaves = []
        try:
            expand(load(m), str(m), leaves)
        except Exception:
            continue
        d = dict(leaves)
        for r in rs:
            blob = d.get(r["path"])
            if blob is not None and len(blob) == r["len"]:
                yield r["path"], blob, r


def main():
    uniq: dict[bytes, int] = {}
    order: list[bytes] = []
    per_bank = {}
    prefix_ref = None
    prefix_common = None
    nb = 0
    for path, blob, info in bank_blobs():
        b = info["bitmaps"]
        n = info["count"]
        ids = []
        for g in range(n):
            bm = blob[b + g * 24: b + g * 24 + 24]
            k = uniq.get(bm)
            if k is None:
                k = len(order)
                uniq[bm] = k
                order.append(bm)
            ids.append(k)
        per_bank[path] = {"ids": ids, "widths": list(blob[info["widths"]:info["widths"] + n])}
        if prefix_ref is None:
            prefix_ref = ids
            prefix_common = len(ids)
        else:
            c = 0
            while c < min(prefix_common, len(ids)) and prefix_ref[c] == ids[c]:
                c += 1
            prefix_common = c
        nb += 1
    print("banks", nb, "unique glyphs", len(order), "common prefix", prefix_common)
    cnt = Counter()
    for v in per_bank.values():
        for g in set(v["ids"]):
            cnt[g] += 1
    print("glyphs present in >=90% of banks:", sum(1 for g, c in cnt.items() if c >= nb * 0.9))
    with open(OUT, "wb") as f:
        pickle.dump({"glyphs": order, "banks": per_bank, "prefix": prefix_common}, f)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
