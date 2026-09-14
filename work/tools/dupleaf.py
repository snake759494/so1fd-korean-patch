"""Are any leaf paths duplicated inside a member?

`leaves[path] = node` keeps the last node with that path, while tree.mark()
finds the first - so a duplicate means we read one leaf and write another.
"""
from __future__ import annotations

import pickle
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
import tree

BUILD = r"D:\psp\rom\SO1\work\build"


def main():
    ov = sorted(pickle.load(open(os.path.join(BUILD, "overrides.pkl"), "rb")))
    p = Pack()
    hit = []
    for m in ov:
        c = Counter(n.path for n in tree.walk(tree.parse(p.read(m), str(m)))
                    if n.data and not n.kids)
        d = [q for q, k in c.items() if k > 1]
        if d:
            hit.append((m, d[:3], len(d)))
    p.close()
    print(f"members with duplicated leaf paths: {len(hit)} of {len(ov)}")
    for m, d, n in hit[:10]:
        print(f"   member {m}: {n} duplicated, e.g. {d}")


if __name__ == "__main__":
    main()
