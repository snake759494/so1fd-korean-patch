"""Detect bitmap-font-like regions.

A glyph bitmap stored row-major with W bytes per row makes byte[i] and
byte[i+W] strongly correlated (adjacent scanlines of the same glyph), while
adjacent bytes within a row are much less correlated for small glyphs.
Scan windows and report the best stride and its correlation.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

STRIDES = [1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 16, 18, 24, 32, 48, 64]


def corr(a: np.ndarray, s: int) -> float:
    if a.size <= s + 16:
        return 0.0
    x = a[:-s].astype(np.float64)
    y = a[s:].astype(np.float64)
    sx, sy = x.std(), y.std()
    if sx < 1e-9 or sy < 1e-9:
        return 0.0
    return float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))


def analyse(blob: bytes):
    a = np.frombuffer(blob, dtype=np.uint8)
    if a.size < 4096:
        return None
    zero = float((a == 0).mean())
    if zero < 0.05 or zero > 0.97:
        return None
    cs = {s: corr(a, s) for s in STRIDES}
    best = max(cs, key=lambda s: cs[s])
    if best == 1:
        return None
    if cs[best] < 0.35 or cs[best] <= cs[1] + 0.05:
        return None
    return {"zero": round(zero, 3), "stride": best, "corr": round(cs[best], 3),
            "c1": round(cs[1], 3)}


def main():
    OUT = r"D:\psp\rom\SO1\work\unpack"
    manifest = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    rows = []
    # the executable first
    for name, path in (("BOOT.BIN", r"D:\psp\rom\SO1\work\extract\PSP_GAME\SYSDIR\BOOT.BIN"),):
        d = open(path, "rb").read()
        for off in range(0, len(d) - 8192, 8192):
            r = analyse(d[off:off + 16384])
            if r:
                rows.append({"path": f"{name}@0x{off:X}", "len": 16384, **r})
    for rec in manifest:
        i = rec["idx"]
        if i > 5100 and rec.get("sig") in ("BIN:1C000000", "BIN:20000000"):
            continue
        d = load(i)
        if len(d) < 4096:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            r = analyse(blob)
            if r:
                rows.append({"path": p, "len": len(blob), **r})
        if i % 2000 == 0:
            print("..", i, flush=True)
    rows.sort(key=lambda r: -r["corr"])
    print("hits:", len(rows))
    for r in rows[:80]:
        print(f"  {r['path']:<22} len={r['len']:<9} zero={r['zero']:<6} "
              f"stride={r['stride']:<3} corr={r['corr']:<6} c1={r['c1']}")
    json.dump(rows, open(r"D:\psp\rom\SO1\work\font_cands.json", "w"), indent=1)


if __name__ == "__main__":
    main()
