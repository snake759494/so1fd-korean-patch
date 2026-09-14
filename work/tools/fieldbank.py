"""Star Ocean: First Departure text bank (field-map chunk type 1 and friends).

Tail layout, byte-packed (no alignment padding is guaranteed):
    u32 num_glyphs
    u32 height (= 12)
    u8  width[num_glyphs]
    u8  bitmap[num_glyphs][24]     12 rows x 2 bytes, MSB-first, 12 px wide

The unpacked blob can carry a few trailing bytes, and the bitmap array is
2-byte aligned, so the exact base is resolved by checking that every row's low
nibble is unused (a 12-pixel row leaves the bottom 4 bits of byte 1 clear).

A message is a u16 stream; code C draws glyph C - 0x101.
"""
from __future__ import annotations

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GLYPH_BYTES = 24
CODE_BASE = 0x101


def _clean(d: bytes, base: int, count: int) -> int:
    bad = 0
    for i in range(count * 12):
        if d[base + i * 2 + 1] & 0x0F:
            bad += 1
            if bad > 2:
                break
    return bad


def fonts(d: bytes):
    """Every font block in the blob: header `u32 count, u32 12` anywhere."""
    import numpy as np
    n = len(d)
    if n < 64:
        return []
    a = np.frombuffer(d, dtype=np.uint8)
    cand = np.flatnonzero((a[4:n - 4] == 12) & (a[5:n - 3] == 0) &
                          (a[6:n - 2] == 0) & (a[7:n - 1] == 0))
    out = []
    for p in cand.tolist():
        cnt = int.from_bytes(d[p:p + 4], "little")
        if not (16 <= cnt <= 8000):
            continue
        wid = p + 8
        base = wid + cnt
        if base + cnt * GLYPH_BYTES > n + 3:
            continue
        if max(d[wid:wid + cnt], default=99) > 12:
            continue
        for k in (0, -1, 1, -2, 2):
            b = base + k
            if b < 0 or b + cnt * GLYPH_BYTES > n:
                continue
            if _clean(d, b, cnt) == 0:
                out.append({"count": cnt, "hdr": p, "widths": b - cnt,
                            "bitmaps": b, "end": b + cnt * GLYPH_BYTES})
                break
    # drop nested/overlapping duplicates, keep the largest
    out.sort(key=lambda f: -f["count"])
    kept = []
    for f in out:
        if not any(k["hdr"] <= f["hdr"] < k["end"] for k in kept):
            kept.append(f)
    kept.sort(key=lambda f: f["hdr"])
    return kept


def font(d: bytes):
    fs = fonts(d)
    return max(fs, key=lambda f: f["count"]) if fs else None


def glyph_rows(d: bytes, info: dict, index: int):
    o = info["bitmaps"] + index * GLYPH_BYTES
    return [(d[o + r * 2] << 8) | d[o + r * 2 + 1] for r in range(12)]


def draw_codes(d, info, codes, img, x, y):
    px = img.load()
    for c in codes:
        gi = c - CODE_BASE
        if 0 <= gi < info["count"]:
            for r, v in enumerate(glyph_rows(d, info, gi)):
                for k in range(12):
                    if (v >> (15 - k)) & 1 and 0 <= x + k < img.width and 0 <= y + r < img.height:
                        px[x + k, y + r] = 255
            w = d[info["widths"] + gi] if 0 <= info["widths"] + gi < len(d) else 12
            x += w if w else 12
        else:
            x += 6
        if x > img.width - 14:
            break
    return x


if __name__ == "__main__":
    from expand import expand, load
    for a in sys.argv[1:]:
        m = int(a)
        leaves = []
        expand(load(m), str(m), leaves)
        for path, blob in leaves:
            info = font(blob)
            if info:
                print(path, len(blob), info)
