"""Render a patched font bank to PNG.

Two sheets: the glyphs this patch replaced (the Hangul we inserted, shown
against what used to be in the same slot), and the whole bank so the Hangul
can be seen sitting among the original Japanese.
"""
from __future__ import annotations

import json
import pickle
import sys
import os

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
import tree
from autopatch import shell_depth

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"
OUT = (r"C:\Users\Jay\AppData\Local\Temp\claude\D--psp-rom-SO1"
       r"\ca9f157d-f420-4933-b78c-7de1a63c64e0\scratchpad")


def bits(b24):
    rows = []
    for r in range(12):
        v = (b24[r * 2] << 8) | b24[r * 2 + 1]
        rows.append([(v >> (15 - c)) & 1 for c in range(12)])
    return rows


def font_leaf(pack, member, fi):
    root = tree.parse(pack.read(member), str(member))
    k = shell_depth(root)
    pre = str(member)
    want = pre + "!" * k + fi["path"][len(pre):]
    for n in tree.walk(root):
        if n.path == want and n.data and not n.kids:
            return n.data
    return None


def sheet(glyphs, cols, scale, gap, title, path, labels=None):
    cell = 12 * scale + gap
    rows = (len(glyphs) + cols - 1) // cols
    W = cols * cell + gap
    H = rows * cell + gap + 28
    im = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(im)
    d.text((gap, 8), title, fill=(210, 210, 220))
    for i, g in enumerate(glyphs):
        ox = gap + (i % cols) * cell
        oy = 28 + gap + (i // cols) * cell
        d.rectangle([ox, oy, ox + 12 * scale - 1, oy + 12 * scale - 1],
                    fill=(38, 38, 44))
        for y, row in enumerate(bits(g)):
            for x, on in enumerate(row):
                if on:
                    d.rectangle([ox + x * scale, oy + y * scale,
                                 ox + (x + 1) * scale - 1,
                                 oy + (y + 1) * scale - 1], fill=(235, 235, 240))
    im.save(path)
    return path


def main():
    member = int(sys.argv[1]) if len(sys.argv) > 1 else 2337
    build = sys.argv[2] if len(sys.argv) > 2 else r"D:\psp\rom\SO1\work\build\so1pack_v09.bin"
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    key, count = inv["member_font"][member]
    fi = cat[key]
    a, b = Pack(), Pack(build)
    da, db = font_leaf(a, member, fi), font_leaf(b, member, fi)
    a.close()
    b.close()
    bm = fi["bitmaps"]
    orig = [da[bm + g * 24: bm + g * 24 + 24] for g in range(count)]
    new = [db[bm + g * 24: bm + g * 24 + 24] for g in range(count)]
    changed = [g for g in range(count) if orig[g] != new[g]]
    os.makedirs(OUT, exist_ok=True)
    p1 = sheet([new[g] for g in changed], 24, 6, 4,
               f"member {member}: {len(changed)} inserted Hangul glyphs (Galmuri11, 12px)",
               os.path.join(OUT, f"hangul_{member}.png"))
    p2 = sheet([orig[g] for g in changed], 24, 6, 4,
               f"member {member}: what those {len(changed)} slots held before",
               os.path.join(OUT, f"before_{member}.png"))
    p3 = sheet(new, 32, 4, 3,
               f"member {member}: whole bank after patch ({count} glyphs)",
               os.path.join(OUT, f"bank_{member}.png"))
    print(p1)
    print(p2)
    print(p3)
    print("changed:", len(changed), "of", count)


if __name__ == "__main__":
    main()
