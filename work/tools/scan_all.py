"""Catalogue every font, build the global glyph inventory, and extract text.

A member's messages live in one leaf and its font in another, so fonts are
collected per member and the largest one is used to bound the code range.
"""
from __future__ import annotations

import json
import pickle
import sys
import os
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load
from fieldbank import fonts
import canon

CAT = r"D:\psp\rom\SO1\work\banks.json"
INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
TSV = r"D:\psp\rom\SO1\work\text.tsv"
MINRUN = 2


def find_runs(blob: bytes, count: int, minrun=MINRUN):
    n = len(blob)
    if n < 4:
        return []
    a = np.frombuffer(blob, dtype=np.uint8).astype(np.int32)
    code = a[:-1] | (a[1:] << 8)
    valid = (code >= 0x101) & (code < 0x101 + count)
    L = np.zeros(n, dtype=np.int32)
    v = valid.tolist()
    for p in range(len(v) - 1, -1, -1):
        if v[p]:
            L[p] = 1 + (L[p + 2] if p + 2 < n else 0)
    order = np.argsort(-L, kind="stable")
    taken = bytearray(n + 2)
    out = []
    for p in order.tolist():
        ln = int(L[p])
        if ln < minrun:
            break
        if any(taken[p:p + ln * 2]):
            continue
        taken[p:p + ln * 2] = b"\x01" * (ln * 2)
        out.append((p, [int(code[p + 2 * k]) for k in range(ln)]))
    out.sort()
    return out


def main():
    uniq: dict[bytes, int] = {}
    order: list[bytes] = []
    cat = []
    member_font = {}
    bank_ids = {}
    for i in range(14320):
        try:
            d = load(i)
        except Exception:
            continue
        if len(d) < 512:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        best = None
        for p, blob in leaves:
            for f in fonts(blob):
                ids = []
                b = f["bitmaps"]
                for g in range(f["count"]):
                    bm = blob[b + g * 24: b + g * 24 + 24]
                    k = uniq.get(bm)
                    if k is None:
                        k = len(order)
                        uniq[bm] = k
                        order.append(bm)
                    ids.append(k)
                key = f"{p}#{f['hdr']:X}"
                bank_ids[key] = {"ids": ids,
                                 "widths": list(blob[f["widths"]:f["widths"] + f["count"]])}
                cat.append({"key": key, "path": p, "member": i, "len": len(blob), **f})
                if best is None or f["count"] > best[1]:
                    best = (key, f["count"])
        if best:
            member_font[i] = best
        if i % 2000 == 0:
            print("..", i, flush=True)

    # canonical labels from field banks (272-glyph shared prefix)
    votes: dict[int, Counter] = {}
    for r in cat:
        if not r["path"].endswith("/t1!"):
            continue
        ids = bank_ids[r["key"]]["ids"]
        for idx, g in enumerate(ids[:272]):
            votes.setdefault(g, Counter())[canon.PREFIX[idx]] += 1
    label = {g: c.most_common(1)[0][0] for g, c in votes.items()}

    json.dump(cat, open(CAT, "w"), indent=1)
    pickle.dump({"glyphs": order, "banks": bank_ids, "canon": label,
                 "member_font": member_font}, open(INV, "wb"))
    print("fonts", len(cat), "members with fonts", len(member_font),
          "unique glyphs", len(order), "canonical labels", len(label))

    # ---- text extraction ----
    rows = []
    unknown = Counter()
    for i, (key, count) in sorted(member_font.items()):
        leaves = []
        try:
            expand(load(i), str(i), leaves)
        except Exception:
            continue
        ids = bank_ids[key]["ids"]
        for p, blob in leaves:
            if len(blob) < 4:
                continue
            for off, codes in find_runs(blob, count):
                s = []
                unk = 0
                for c in codes:
                    g = ids[c - 0x101]
                    ch = label.get(g)
                    if ch is None:
                        ch = "\ue000"
                        unknown[g] += 1
                        unk += 1
                    s.append(ch)
                rows.append((p, key, off, len(codes), unk, "".join(s)))
        if i % 500 == 0:
            print("text..", i, flush=True)
    with open(TSV, "w", encoding="utf-8") as f:
        f.write("path\tfont\toffset\tlen\tunknown\ttext\n")
        for p, key, off, n, unk, txt in rows:
            f.write(f"{p}\t{key}\t{off}\t{n}\t{unk}\t{txt}\n")
    tot = sum(r[3] for r in rows)
    unk = sum(r[4] for r in rows)
    print(f"strings {len(rows)}  chars {tot}  unknown {unk} ({unk / max(tot,1):.1%})")
    json.dump({str(k): v for k, v in unknown.most_common()},
              open(r"D:\psp\rom\SO1\work\unknown_glyphs.json", "w"), indent=1)
    print("distinct unknown glyphs:", len(unknown))


if __name__ == "__main__":
    main()
