"""Identify the game's 12x12 glyph bitmaps as Japanese characters.

Two things make this both fast and accurate:
  * Hamming distance via one BLAS matmul  (|a| + |b| - 2 a.b)
  * bounding-box normalisation, so a reference glyph only has to match in
    shape, not in where FreeType happened to place it.
Monochrome rendering (mode "1") lets FreeType use the embedded 12px bitmap
strikes that MS Gothic ships, which is what a 12-dot game font resembles.
"""
from __future__ import annotations

import pickle
import sys
import os
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GLYPHS = r"D:\psp\rom\SO1\work\glyphs.pkl"
OUT = r"D:\psp\rom\SO1\work\glyph_labels.pkl"
FONTS = [(r"C:\Windows\Fonts\msgothic.ttc", 12), (r"C:\Windows\Fonts\msgothic.ttc", 11),
         (r"C:\Windows\Fonts\msgothic.ttc", 13), (r"C:\Windows\Fonts\msmincho.ttc", 12),
         (r"C:\Windows\Fonts\meiryo.ttc", 12), (r"C:\Windows\Fonts\YuGothM.ttc", 12),
         (r"C:\Windows\Fonts\malgun.ttf", 12)]


def decode_glyphs(blobs):
    a = np.frombuffer(b"".join(blobs), dtype=np.uint8).reshape(len(blobs), 24)
    v = (a[:, 0::2].astype(np.uint16) << 8) | a[:, 1::2]
    return ((v[:, :, None] >> np.arange(15, 3, -1)[None, None, :]) & 1).astype(np.uint8)


def normalise(bits):
    """Copy any bitmap into a 12x12 box with its ink bounding box at (0,0)."""
    out = np.zeros((12, 12), dtype=np.float32)
    ys, xs = np.nonzero(bits)
    if ys.size == 0:
        return out.ravel()
    h = min(12, ys.max() - ys.min() + 1)
    w = min(12, xs.max() - xs.min() + 1)
    out[:h, :w] = bits[ys.min():ys.min() + h, xs.min():xs.min() + w]
    return out.ravel()


def candidates() -> list[str]:
    out, seen = [], set()

    def add(ch):
        if ch not in seen:
            seen.add(ch)
            out.append(ch)

    for c in range(0x20, 0x7F):
        add(chr(c))
    for c in range(0xFF61, 0xFFA0):
        add(chr(c))
    for c in range(0x3041, 0x3100):
        add(chr(c))
    for c in range(0x3000, 0x3040):
        add(chr(c))
    for c in range(0xFF01, 0xFF61):
        add(chr(c))
    for c in (0x2010, 0x2015, 0x2016, 0x2018, 0x2019, 0x201C, 0x201D, 0x2020, 0x2021,
              0x2025, 0x2026, 0x2030, 0x2032, 0x2033, 0x203B, 0x2103, 0x2116, 0x2190,
              0x2191, 0x2192, 0x2193, 0x21D2, 0x21D4, 0x221E, 0x2260, 0x25A0, 0x25A1,
              0x25B2, 0x25B3, 0x25BC, 0x25BD, 0x25C6, 0x25C7, 0x25CB, 0x25CE, 0x25CF,
              0x2605, 0x2606, 0x2640, 0x2642, 0x266A, 0x3012, 0x00A7, 0x00B0, 0x00B1,
              0x00D7, 0x00F7, 0x00A5):
        add(chr(c))
    for hi in range(0x88, 0xF0):
        for lo in range(0x40, 0xFD):
            if lo == 0x7F:
                continue
            try:
                ch = bytes((hi, lo)).decode("cp932")
            except Exception:
                continue
            if len(ch) == 1 and 0x4E00 <= ord(ch) <= 0x9FFF:
                add(ch)
    return out


def build_variants(chars):
    fonts = []
    for path, size in FONTS:
        if os.path.exists(path):
            try:
                fonts.append(ImageFont.truetype(path, size))
            except Exception:
                pass
    print("reference fonts:", len(fonts), flush=True)
    vecs, labels = [], []
    canvas = Image.new("1", (28, 28), 0)
    draw = ImageDraw.Draw(canvas)
    for ch in chars:
        for f in fonts:
            draw.rectangle([0, 0, 27, 27], fill=0)
            try:
                draw.text((8, 8), ch, font=f, fill=1)
            except Exception:
                continue
            a = np.asarray(canvas, dtype=np.uint8)
            if not a.any():
                continue
            vecs.append(normalise(a))
            labels.append(ch)
    return np.array(vecs, dtype=np.float32), labels


def main():
    t0 = time.time()
    data = pickle.load(open(GLYPHS, "rb"))
    raw = decode_glyphs(data["glyphs"])
    G = np.array([normalise(b) for b in raw], dtype=np.float32)
    gsum = G.sum(axis=1)
    print("game glyphs:", G.shape, flush=True)

    chars = candidates()
    print("candidates:", len(chars), flush=True)
    V, labels = build_variants(chars)
    print("variants:", V.shape, f"({time.time() - t0:.1f}s)", flush=True)
    vsum = V.sum(axis=1)

    best = np.full(G.shape[0], 1e9, dtype=np.float32)
    argb = np.zeros(G.shape[0], dtype=np.int64)
    CH = 16384
    for s in range(0, V.shape[0], CH):
        Vc = V[s:s + CH]
        dist = gsum[:, None] + vsum[None, s:s + CH] - 2.0 * (G @ Vc.T)
        m = dist.argmin(axis=1)
        v = dist[np.arange(G.shape[0]), m]
        better = v < best
        best[better] = v[better]
        argb[better] = m[better] + s
    label = [labels[i] for i in argb]
    dist = best.astype(int).tolist()
    pickle.dump({"labels": label, "dist": dist}, open(OUT, "wb"))
    for thr in (0, 2, 4, 8, 12, 16):
        print(f"  distance <= {thr}: {sum(1 for d in dist if d <= thr)} / {len(dist)}")
    print("elapsed %.1fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
