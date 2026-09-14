"""Do several tree nodes share one catalogue path?

If they do, "first match wins" and "last match wins" read different bytes for
the same bank - which is how a blank-slot census can disagree with itself.
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


def main():
    member = int(sys.argv[1]) if len(sys.argv) > 1 else 1709
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    key, count = inv["member_font"][member]
    fi = cat[key]
    p = Pack()
    root = tree.parse(p.read(member), str(member))
    p.close()
    k = shell_depth(root)
    pre = str(member)
    hits = []
    seen = Counter()
    for n in tree.walk(root):
        q = n.path
        if q.startswith(pre + "!" * k):
            q = pre + q[len(pre) + k:]
        seen[q] += 1
        if q == fi["path"]:
            hits.append(n)
    print(f"member {member} bank {key} path {fi['path']} count={count}")
    print(f"  nodes matching that path: {len(hits)}")
    bm = fi["bitmaps"]
    for i, n in enumerate(hits):
        d = n.data or b""
        blank = sum(1 for g in range(count) if not any(d[bm + g * 24: bm + g * 24 + 24]))
        print(f"    [{i}] kind={n.kind} len={len(d)} needs={bm + count * 24}"
              f" blank={blank}")
    dups = [q for q, c in seen.items() if c > 1]
    print(f"  duplicated paths in this member: {len(dups)}")


if __name__ == "__main__":
    main()
