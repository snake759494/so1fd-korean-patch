"""Prove the patch changed no text it did not mean to change.

Replacing a glyph bitmap silently rewrites every string that still points at
that slot - that is how Japanese dialogue came back as stray Hangul, and no
amount of container checking can see it.  The test that does see it:

    a byte pair we did NOT write, that still decodes to a glyph whose bitmap
    we DID replace, is a corrupted character.

Anything this reports would render as the wrong letter on screen.
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
from autopatch import shell_depth, load_rows

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"
BUILD = r"D:\psp\rom\SO1\work\build"


def leaves_of(pack, member):
    """Leaves keyed by their real tree path, and the font leaf's path."""
    root = tree.parse(pack.read(member), str(member))
    k = shell_depth(root)
    pre = str(member)
    out = {n.path: n.data for n in tree.walk(root) if n.data and not n.kids}
    return out, (lambda p: pre + "!" * k + p[len(pre):])


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BUILD, "so1pack.bin")
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    ov = pickle.load(open(os.path.join(BUILD, "overrides.pkl"), "rb"))
    label = inv.get("label") or inv["canon"]
    rows = load_rows()
    mode_of = {}
    for r in rows:
        m = int(r["path"].split("/")[0])
        mode_of.setdefault(m, r["mode"])

    a = Pack()
    b = Pack(path)
    st = Counter()
    examples = []
    for m in sorted(ov):
        key, count = inv["member_font"][m]
        fi = cat[key]
        mode = mode_of.get(m, codemap.PAGED)
        la, to_tree = leaves_of(a, m)
        lb, _ = leaves_of(b, m)
        fpath = to_tree(fi["path"])
        fa, fb = la.get(fpath), lb.get(fpath)
        if not fa or not fb:
            st["no_font_leaf"] += 1
            continue
        bm = fi["bitmaps"]
        changed = np.zeros(count, dtype=bool)
        for g in range(count):
            if fa[bm + g * 24: bm + g * 24 + 24] != fb[bm + g * 24: bm + g * 24 + 24]:
                changed[g] = True
        st["glyphs_replaced"] += int(changed.sum())
        if not changed.any():
            continue
        for p, db in lb.items():
            da = la.get(p)
            if not da or len(da) != len(db) or len(db) < 2:
                continue
            x = np.frombuffer(da, dtype=np.uint8)
            y = np.frombuffer(db, dtype=np.uint8)
            slot = (y[:-1].astype(np.int32) | (y[1:].astype(np.int32) << 8)) - 0x101
            idx = slot if mode == codemap.FLAT else slot - 128 * (slot // 256)
            ok = (slot >= 0) & (idx >= 0) & (idx < count)
            if p == fpath:
                ok[max(0, fi["hdr"] - 1): fi["end"]] = False
            untouched = (x[:-1] == y[:-1]) & (x[1:] == y[1:])
            hit = ok & untouched
            if hit.any():
                bad = np.flatnonzero(hit & changed[np.clip(idx, 0, count - 1)])
                if bad.size:
                    st["corrupted_refs"] += int(bad.size)
                    if len(examples) < 8:
                        o = int(bad[0])
                        g = int(idx[o])
                        examples.append((m, p, o, g, label.get(
                            inv["banks"][key]["ids"][g])))
    a.close()
    b.close()
    print(f"{os.path.basename(path)}: members {len(ov)}")
    print(f"  glyph bitmaps replaced      : {st['glyphs_replaced']}")
    print(f"  CORRUPTED references        : {st['corrupted_refs']}")
    for m, p, o, g, ch in examples:
        print(f"     member {m} leaf {p} offset {o} -> glyph {g} (was {ch!r})")


if __name__ == "__main__":
    main()
