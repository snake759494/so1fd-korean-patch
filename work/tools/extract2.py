"""Extract text from the script/message leaves (skip geometry & textures).

Two things matter for correctness:
  * a run can start at any byte, so the alignment is chosen by kana yield;
  * a bank addresses its font either flat or in 128-glyph pages
    (index = slot - 128*(slot//256)), decided per member by kana yield too.

Everything hot is vectorised with numpy, so runtime is bandwidth-bound and
independent of core count.
"""
from __future__ import annotations

import json
import pickle
import re
import sys
import os
import time
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load
import codemap

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
TSV = r"D:\psp\rom\SO1\work\text.tsv"
SKIP = re.compile(r"/t(2|13|14|15|16|17|18|20)(!|/|$)")
MINRUN = 3


def slot_index(slots: np.ndarray, mode: str) -> np.ndarray:
    if mode == codemap.FLAT:
        return slots
    return slots - 128 * (slots // 256)


def _runs_for_parity(valid: np.ndarray, kana: np.ndarray):
    n = valid.size
    if n == 0:
        z = np.empty(0, np.int64)
        return z, z, z
    nxt = np.where(valid, n, np.arange(n))
    nxt = np.minimum.accumulate(nxt[::-1])[::-1]
    length = nxt - np.arange(n)
    length[~valid] = 0
    kcum = np.concatenate(([0], np.cumsum(kana)))
    kcount = kcum[nxt] - kcum[np.arange(n)]
    starts = np.flatnonzero(valid & np.concatenate(([True], ~valid[:-1])))
    return starts, length[starts], kcount[starts]


def find_runs(blob, count, ids, is_kana, mode, minrun=MINRUN):
    n = len(blob)
    if n < 4:
        return []
    a = np.frombuffer(blob, dtype=np.uint8).astype(np.int32)
    code = a[:-1] | (a[1:] << 8)
    slot = code - 0x101
    idx = slot_index(slot, mode)
    ok = (slot >= 0) & (idx >= 0) & (idx < count)
    gi = np.where(ok, idx, 0)
    kana = np.where(ok, is_kana[ids[gi]], False)

    cands = []
    for par in (0, 1):
        s, ln, kc = _runs_for_parity(ok[par::2], kana[par::2])
        keep = ln >= minrun
        for p, l, c in zip(s[keep] * 2 + par, ln[keep], kc[keep]):
            cands.append((int(c), int(l), int(p)))
    if not cands:
        return []
    cands.sort(key=lambda t: (-t[0], -t[1]))
    taken = np.zeros(n + 2, dtype=bool)
    out = []
    for c, l, p in cands:
        if taken[p:p + l * 2].any():
            continue
        taken[p:p + l * 2] = True
        out.append((p, [int(idx[p + 2 * j]) for j in range(l)]))
    out.sort()
    return out


def main():
    t0 = time.time()
    inv = pickle.load(open(INV, "rb"))
    label = inv.get("label") or inv["canon"]
    bank_ids, member_font = inv["banks"], inv["member_font"]
    is_kana = np.zeros(len(inv["glyphs"]), dtype=bool)
    for g, ch in label.items():
        if ch and 0x3041 <= ord(ch[0]) <= 0x30FF:
            is_kana[g] = True
    ids_cache = {k: np.asarray(v["ids"], dtype=np.int64) for k, v in bank_ids.items()}

    rows = []
    unknown = Counter()
    modes = Counter()
    for i, (key, count) in sorted(member_font.items()):
        leaves = []
        try:
            expand(load(i), str(i), leaves)
        except Exception:
            continue
        leaves = [(p, b) for p, b in leaves if len(b) >= 8 and not SKIP.search(p)]
        if not leaves:
            continue
        ids = ids_cache[key]
        hist = Counter()
        for p, blob in leaves:
            a = np.frombuffer(blob, dtype=np.uint8).astype(np.int32)
            if a.size < 2:
                continue
            code = a[:-1] | (a[1:] << 8)
            slot = code - 0x101
            sel = slot[(slot >= 0) & (slot < 2 * count)]
            hist.update(sel.tolist())
        mode = codemap.detect(hist, ids, is_kana, count)
        modes[mode] += 1
        for p, blob in leaves:
            for off, indices in find_runs(blob, count, ids, is_kana, mode):
                s, unk = [], 0
                for gidx in indices:
                    g = int(ids[gidx])
                    ch = label.get(g)
                    if ch is None:
                        ch = "\ue000"
                        unknown[g] += 1
                        unk += 1
                    s.append(ch)
                rows.append((p, key, mode, off, len(indices), unk, "".join(s)))
        if i % 2000 == 0:
            print("..", i, f"{time.time() - t0:.0f}s", flush=True)
    with open(TSV, "w", encoding="utf-8") as f:
        f.write("path\tfont\tmode\toffset\tlen\tunknown\ttext\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    tot = sum(r[4] for r in rows)
    unk = sum(r[5] for r in rows)
    print(f"strings {len(rows)}  chars {tot}  unknown {unk} ({unk / max(tot,1):.1%})"
          f"  modes {dict(modes)}  elapsed {time.time() - t0:.0f}s")
    json.dump({str(k): v for k, v in unknown.most_common()},
              open(r"D:\psp\rom\SO1\work\unknown_glyphs.json", "w"), indent=1)
    print("distinct unknown glyphs:", len(unknown))


if __name__ == "__main__":
    main()
