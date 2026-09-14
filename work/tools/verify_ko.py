"""Render translated strings straight out of the built so1pack, as a check."""
from __future__ import annotations

import json
import pickle
import sys
import os

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
from locate import locate
import codemap

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"
PACK = r"D:\psp\rom\SO1\work\build\so1pack.bin"


def main():
    tr = json.load(open(sys.argv[1], encoding="utf-8"))
    member = int(sys.argv[2])
    items = [t for t in tr if int(t["member"]) == member]
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    key, count = inv["member_font"][member]
    fi = cat[key]
    p = Pack(PACK)
    d = p.read(member)
    p.close()
    loc = locate(d, str(member))
    fbase = loc[fi["path"]][0]
    bmp, wid = fbase + fi["bitmaps"], fbase + fi["widths"]

    img = Image.new("L", (760, 15 * len(items)), 0)
    px = img.load()
    for row, t in enumerate(items):
        base = loc[t["path"]][0] + int(t["off"])
        x, y = 0, row * 15
        for j in range(int(t["len"])):
            code = d[base + j * 2] | (d[base + j * 2 + 1] << 8)
            gi = codemap.to_index(code - 0x101, codemap.PAGED)
            if not (0 <= gi < count):
                x += 6
                continue
            o = bmp + gi * 24
            for r in range(12):
                v = (d[o + r * 2] << 8) | d[o + r * 2 + 1]
                for c in range(12):
                    if (v >> (15 - c)) & 1 and x + c < img.width:
                        px[x + c, y + r] = 255
            x += max(d[wid + gi], 1)
            if x > 745:
                break
    out = rf"D:\psp\rom\SO1\work\verify_{member}.png"
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(out)
    print("->", out, len(items), "strings")


if __name__ == "__main__":
    main()
