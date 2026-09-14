"""Deep equivalence check between the original and the built so1pack.

The black-screen regression came from a rebuild that silently changed the SLZ
container shape, so this checks exactly that, on the *stored* member bytes:
same container tree, same per-member SLZ modes and decoded sizes, same chain
lengths, same member length - and every decoded leaf byte-identical except the
ones we meant to edit.
"""
from __future__ import annotations

import pickle
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
import slz
import tree

PACK = r"D:\psp\rom\SO1\work\build\so1pack.bin"
BUILD = r"D:\psp\rom\SO1\work\build"


def shape(node):
    out = []

    def walk(n):
        item = [n.kind, len(n.kids)]
        if n.kind == "slz":
            try:
                ch = slz.parse_chain(n.data)
            except Exception as e:
                item.append(f"BADSLZ:{e}")
            else:
                item.append(tuple((m, u) for m, _c, u, _nx, _o in ch))
        out.append(tuple(item))
        for k in n.kids:
            walk(k)
    walk(node)
    return out


def main():
    ov = pickle.load(open(os.path.join(BUILD, "overrides.pkl"), "rb"))
    a = Pack()
    b = Pack(PACK)
    stats = Counter()
    problems = []
    for m in sorted(ov):
        old, new = a.read(m), b.read(m)
        if len(old) != len(new):
            problems.append((m, f"member length {len(old)} -> {len(new)}"))
            stats["len_diff"] += 1
            continue
        try:
            to = tree.parse(old, str(m))
            tn = tree.parse(new, str(m))
        except Exception as e:
            problems.append((m, f"parse: {e}"))
            stats["parse_fail"] += 1
            continue
        so, sn = shape(to), shape(tn)
        if so != sn:
            i = next((k for k, (x, y) in enumerate(zip(so, sn)) if x != y), None)
            problems.append((m, f"shape node {i}: {so[i] if i is not None else ''}"
                                f" != {sn[i] if i is not None else ''}"))
            stats["shape_diff"] += 1
            continue
        lo = {n.path: n.data for n in tree.walk(to) if n.kind == "raw"}
        ln = {n.path: n.data for n in tree.walk(tn) if n.kind == "raw"}
        if set(lo) != set(ln):
            problems.append((m, "leaf set differs"))
            stats["leafset_diff"] += 1
            continue
        changed = [k for k in lo if lo[k] != ln[k]]
        for k in changed:
            if len(lo[k]) != len(ln[k]):
                problems.append((m, f"leaf {k} length {len(lo[k])} -> {len(ln[k])}"))
                stats["leaf_len_diff"] += 1
        stats["ok"] += 1
        stats["changed_leaves"] += len(changed)
        if not changed:
            stats["no_change"] += 1
    a.close()
    b.close()
    print(f"members {len(ov)}: ok {stats['ok']}  len_diff {stats['len_diff']}  "
          f"parse_fail {stats['parse_fail']}  shape_diff {stats['shape_diff']}  "
          f"leafset_diff {stats['leafset_diff']}  leaf_len_diff {stats['leaf_len_diff']}")
    print(f"changed leaves {stats['changed_leaves']}, members with no change {stats['no_change']}")
    for m, msg in problems[:15]:
        print("  ", m, msg)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
