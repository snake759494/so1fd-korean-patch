"""Cross-check hand-read labels against the automatic bitmap matcher.

Agreement is strong evidence; disagreement flags the glyph for a second look.
"""
from __future__ import annotations

import json
import pickle
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from identify import decode_glyphs, normalise, candidates, build_variants

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
UNK = r"D:\psp\rom\SO1\work\unknown_glyphs.json"


def main():
    inv = pickle.load(open(INV, "rb"))
    manual = inv.get("manual", {})
    raw = decode_glyphs(inv["glyphs"])
    G = np.array([normalise(b) for b in raw], dtype=np.float32)
    gsum = G.sum(axis=1)
    chars = candidates()
    V, labels = build_variants(chars)
    vsum = V.sum(axis=1)
    TOP = 5
    best = np.full((G.shape[0], TOP), 1e9, dtype=np.float32)
    arg = np.zeros((G.shape[0], TOP), dtype=np.int64)
    CH = 16384
    for s in range(0, V.shape[0], CH):
        Vc = V[s:s + CH]
        dist = gsum[:, None] + vsum[None, s:s + CH] - 2.0 * (G @ Vc.T)
        k = min(TOP, dist.shape[1])
        idx = np.argpartition(dist, k - 1, axis=1)[:, :k]
        val = np.take_along_axis(dist, idx, axis=1)
        allv = np.concatenate([best, val], axis=1)
        alli = np.concatenate([arg, idx + s], axis=1)
        o = np.argsort(allv, axis=1)[:, :TOP]
        best = np.take_along_axis(allv, o, axis=1)
        arg = np.take_along_axis(alli, o, axis=1)

    agree = disagree = 0
    flags = []
    for g, ch in manual.items():
        cand = []
        seen = set()
        for j in range(TOP):
            c = labels[arg[g, j]]
            if c not in seen:
                seen.add(c)
                cand.append(c)
        if ch in cand:
            agree += 1
        else:
            disagree += 1
            flags.append({"glyph": int(g), "manual": ch, "auto": cand,
                          "dist": int(best[g, 0])})
    flags.sort(key=lambda f: f["dist"])
    json.dump(flags, open(r"D:\psp\rom\SO1\work\label_flags.json", "w",
                          encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"manual labels: {len(manual)}  agree with top{TOP}: {agree}  disagree: {disagree}")
    for f in flags[:40]:
        print(f"  glyph {f['glyph']:>5} manual={f['manual']} auto={''.join(f['auto'])} d={f['dist']}")


if __name__ == "__main__":
    main()
