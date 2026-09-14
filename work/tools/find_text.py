"""Statistical hunt for glyph-coded text blobs among all expanded leaves.

Real script text in a custom encoding shows up as a byte/word stream whose
value histogram is strongly skewed (a handful of very common codes = kana and
punctuation) while staying inside a narrow numeric range.
"""
from __future__ import annotations

import json
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

OUT = r"D:\psp\rom\SO1\work\unpack"


def score(d: bytes):
    n = len(d) // 2
    if n < 64:
        return None
    vals = struct.unpack("<%dH" % n, d[:n * 2])
    c = Counter(vals)
    distinct = len(c)
    top = c.most_common(12)
    top_share = sum(v for _, v in top) / n
    hi = sum(1 for v in vals if v >= 0x4000) / n
    # text: many distinct symbols, but a skewed head, and values not huge
    return {"n": n, "distinct": distinct, "top_share": top_share, "hi": hi,
            "top": [(hex(k), v) for k, v in top[:6]]}


def main():
    manifest = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    cands = []
    for rec in manifest:
        i = rec["idx"]
        if i > 5100 and rec.get("sig") in ("BIN:1C000000", "BIN:20000000"):
            continue    # audio bulk
        d = load(i)
        if not d:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            s = score(blob)
            if not s:
                continue
            if s["distinct"] >= 60 and 0.15 <= s["top_share"] <= 0.75 and s["hi"] < 0.02:
                cands.append((p, len(blob), s))
    cands.sort(key=lambda c: -c[1])
    print("candidates:", len(cands))
    for p, ln, s in cands[:60]:
        print(f"  {p:<22} {ln:>9} distinct={s['distinct']:<6} top={s['top_share']:.2f} "
              f"{s['top']}")
    json.dump([{"path": p, "len": ln, **s} for p, ln, s in cands],
              open(r"D:\psp\rom\SO1\work\text_cands.json", "w"), indent=1)


if __name__ == "__main__":
    main()
