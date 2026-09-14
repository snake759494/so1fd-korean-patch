"""Check the built so1pack against the retail SLZ container conventions.

The black screen was an alignment fault, not a decoding error: retail always
rounds a chain link up to 4 so the next 16-byte header lands on an aligned
address, and MIPS faults on an unaligned u32 load.  Decoding the stream cannot
catch that, so it gets its own check.
"""
from __future__ import annotations

import pickle
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slz
from so1pack import Pack
import tree

PACK = r"D:\psp\rom\SO1\work\build\so1pack.bin"
BUILD = r"D:\psp\rom\SO1\work\build"


def walk_slz(node, bad, seen):
    if node.kind == "slz" and node.data:
        try:
            chain = slz.parse_chain(node.data)
        except Exception as e:
            bad.append((node.path, f"parse: {e}"))
            return
        for mode, comp, unp, nxt, off in chain:
            seen["members"] += 1
            if off % 4:
                bad.append((node.path, f"member header at {off} is unaligned"))
            if nxt > 1:
                seen["links"] += 1
                if nxt % 4:
                    bad.append((node.path, f"next_rel {nxt} not 4-aligned"))
                if nxt < 16 + comp:
                    bad.append((node.path, f"next_rel {nxt} overlaps payload {comp}"))
            if off + 16 + comp > len(node.data):
                bad.append((node.path, "payload runs past the container"))
    for k in node.kids:
        walk_slz(k, bad, seen)


def headers(node, out):
    """Every SLZ header field in tree order, for comparison against retail."""
    if node.kind == "slz" and node.data:
        try:
            out.append((node.path, tuple(slz.parse_chain(node.data))))
        except Exception as e:
            out.append((node.path, f"parse: {e}"))
    for k in node.kids:
        headers(k, out)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else PACK
    ov = pickle.load(open(os.path.join(BUILD, "overrides.pkl"), "rb"))
    p = Pack(path)
    q = Pack()
    bad = []
    shape = []
    seen = Counter()
    for m in sorted(ov):
        try:
            walk_slz(tree.parse(p.read(m), str(m)), bad, seen)
        except Exception as e:
            bad.append((str(m), f"tree: {e}"))
            continue
        a, b = [], []
        headers(tree.parse(q.read(m), str(m)), a)
        headers(tree.parse(p.read(m), str(m)), b)
        if a != b:
            for (pa, ha), (pb, hb) in zip(a, b):
                if ha != hb:
                    shape.append((m, pa, ha, hb))
                    break
    p.close()
    q.close()
    print(f"{os.path.basename(path)}: {len(ov)} members, "
          f"{seen['members']} slz members, {seen['links']} chain links")
    print("alignment problems:", len(bad))
    for where, msg in bad[:20]:
        print("  ", where, msg)
    print("headers differing from retail:", len(shape))
    for m, pa, ha, hb in shape[:6]:
        print(f"   member {m} {pa}\n      retail {ha}\n      built  {hb}")


if __name__ == "__main__":
    main()
