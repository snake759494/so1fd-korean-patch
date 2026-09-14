"""Extract every glyph-coded string from the text banks as Japanese text.

Strings sit inside script bytecode that has odd-length commands, so a run can
start at any byte, not just an even one.  L[p] = how many valid 2-byte codes
run from p; the segmentation greedily takes the longest non-overlapping runs.
"""
from __future__ import annotations

import json
import pickle
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

CAT = r"D:\psp\rom\SO1\work\banks.json"
INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
OUT = r"D:\psp\rom\SO1\work\text.tsv"
MINRUN = 2


def find_runs(blob: bytes, count: int, minrun=MINRUN):
    n = len(blob)
    a = np.frombuffer(blob, dtype=np.uint8)
    if n < 4:
        return []
    lo = a[:-1].astype(np.int32)
    hi = a[1:].astype(np.int32)
    code = lo | (hi << 8)
    valid = (code >= 0x101) & (code < 0x101 + count)      # index p -> code at p
    L = np.zeros(n, dtype=np.int32)
    for p in range(len(valid) - 1, -1, -1):
        if valid[p]:
            L[p] = 1 + (L[p + 2] if p + 2 < n else 0)
    order = np.argsort(-L, kind="stable")
    taken = np.zeros(n + 2, dtype=bool)
    out = []
    for p in order:
        ln = int(L[p])
        if ln < minrun:
            break
        if taken[p:p + ln * 2].any():
            continue
        taken[p:p + ln * 2] = True
        out.append((int(p), [int(code[p + 2 * k]) for k in range(ln)]))
    out.sort()
    return out


def main():
    cat = json.load(open(CAT))
    inv = pickle.load(open(INV, "rb"))
    canon_label = inv["canon"]
    banks = inv["banks"]
    by_member = {}
    for r in cat:
        by_member.setdefault(r["member"], []).append(r)

    rows = []
    unknown = {}
    for m, rs in sorted(by_member.items()):
        leaves = []
        try:
            expand(load(m), str(m), leaves)
        except Exception:
            continue
        d = dict(leaves)
        for r in rs:
            blob = d.get(r["path"])
            if blob is None or len(blob) != r["len"]:
                continue
            ids = banks[r["path"]]["ids"]
            for off, codes in find_runs(blob, r["count"]):
                s = []
                unk = 0
                for c in codes:
                    g = ids[c - 0x101]
                    ch = canon_label.get(g)
                    if ch is None:
                        ch = "\ue000"
                        unknown[g] = unknown.get(g, 0) + 1
                        unk += 1
                    s.append(ch)
                rows.append((r["path"], off, len(codes), unk, "".join(s)))
        if m % 200 == 0:
            print("..", m, flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("path\toffset\tlen\tunknown\ttext\n")
        for p, off, n, unk, txt in rows:
            f.write(f"{p}\t{off}\t{n}\t{unk}\t{txt}\n")
    tot = sum(n for _, _, n, _, _ in rows)
    unk = sum(u for _, _, _, u, _ in rows)
    print(f"strings {len(rows)}  chars {tot}  unknown {unk} ({unk / max(tot, 1):.1%})")
    print("distinct unknown glyphs:", len(unknown))
    json.dump({str(k): v for k, v in sorted(unknown.items(), key=lambda x: -x[1])},
              open(r"D:\psp\rom\SO1\work\unknown_glyphs.json", "w"), indent=1)


if __name__ == "__main__":
    main()
