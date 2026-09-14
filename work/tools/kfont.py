"""Render Galmuri11 at 12pt into the game's 12x12 1bpp glyph format."""
from __future__ import annotations

import sys
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

GALMURI = r"D:\nds\files (1)\Galmuri11.ttf"
SIZE = 12


def _font(size=SIZE):
    return ImageFont.truetype(GALMURI, size)


def render(ch: str, font=None, dx=0, dy=0) -> np.ndarray:
    """12x12 binary bitmap for one character."""
    font = font or _font()
    img = Image.new("1", (24, 24), 0)
    ImageDraw.Draw(img).text((6 + dx, 6 + dy), ch, font=font, fill=1)
    a = np.asarray(img, dtype=np.uint8)
    ys, xs = np.nonzero(a)
    out = np.zeros((12, 12), dtype=np.uint8)
    if ys.size == 0:
        return out
    # Galmuri11 at 12px puts Hangul ink on rows origin+1..origin+11, so the
    # 12-row cell starts exactly at the text origin.
    top = 6 + dy
    left = 6 + dx
    sub = a[top:top + 12, left:left + 12]
    out[:sub.shape[0], :sub.shape[1]] = sub
    return out


def encode(bits: np.ndarray) -> bytes:
    out = bytearray()
    for r in range(12):
        v = 0
        for c in range(12):
            if bits[r, c]:
                v |= 1 << (15 - c)
        out += bytes((v >> 8, v & 0xFF))
    return bytes(out)


def advance(bits: np.ndarray, full=False) -> int:
    """Advance width, capped at the 12px cell the engine's tables allow."""
    if full:
        return 12
    xs = np.nonzero(bits.any(axis=0))[0]
    return min(12, int(xs.max()) + 2) if xs.size else 4


def sheet(chars, cols=32, scale=4):
    f = _font()
    img = Image.new("L", (cols * 13, ((len(chars) + cols - 1) // cols) * 13), 30)
    px = img.load()
    for i, ch in enumerate(chars):
        b = render(ch, f)
        ox, oy = (i % cols) * 13, (i // cols) * 13
        for y in range(12):
            for x in range(12):
                if b[y, x]:
                    px[ox + x, oy + y] = 255
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


if __name__ == "__main__":
    demo = "가나다라마바사아자차카타파하 안녕하세요 스타오션 첫 출발 0123456789 ABCDEFabcdef 별의 바다"
    demo += "속성 마법 아이템 장비 세이브 불러오기 전투 경험치 레벨 상태 이상 회복"
    s = sheet([c for c in demo if c != " "])
    s.save(r"D:\psp\rom\SO1\work\galmuri_demo.png")
    print("saved galmuri_demo.png", s.size)
