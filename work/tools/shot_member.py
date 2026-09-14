"""Render a member's strings out of the *built* so1pack, as an image."""
from __future__ import annotations

import json
import pickle
import sys
import os

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
from expand import expand
import extract2
import codemap

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"
PACK = r"D:\psp\rom\SO1\work\build\so1pack.bin"


def main():
    member = int(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    label = inv.get("label") or inv["canon"]
    key, count = inv["member_font"][member]
    fi = cat[key]
    ids = np.asarray(inv["banks"][key]["ids"], dtype=np.int64)
    is_kana = np.zeros(len(inv["glyphs"]), dtype=bool)
    for g, ch in label.items():
        if ch and 0x3041 <= ord(ch[0]) <= 0x30FF:
            is_kana[g] = True

    p = Pack(PACK)
    d = p.read(member)
    p.close()
    leaves = []
    expand(d, str(member), leaves)
    blobs = dict(leaves)
    fb = blobs[fi["path"]]
    bmp, wid = fi["bitmaps"], fi["widths"]

    lines = []
    for path, blob in leaves:
        if len(blob) < 8 or extract2.SKIP.search(path):
            continue
        for off, indices in extract2.find_runs(blob, count, ids, is_kana, "paged", 3):
            if path == fi["path"] and off + len(indices) * 2 > fi["hdr"]:
                continue
            lines.append((path, off, len(indices)))
            if len(lines) >= limit:
                break
        if len(lines) >= limit:
            break

    img = Image.new("L", (760, 15 * max(1, len(lines))), 0)
    px = img.load()
    for row, (path, off, n) in enumerate(lines):
        b = blobs[path]
        x, y = 0, row * 15
        for j in range(n):
            code = b[off + j * 2] | (b[off + j * 2 + 1] << 8)
            gi = codemap.to_index(code - 0x101, codemap.PAGED)
            if not (0 <= gi < count):
                x += 6
                continue
            o = bmp + gi * 24
            for r in range(12):
                v = (fb[o + r * 2] << 8) | fb[o + r * 2 + 1]
                for c in range(12):
                    if (v >> (15 - c)) & 1 and x + c < img.width:
                        px[x + c, y + r] = 255
            x += max(fb[wid + gi], 1)
            if x > 745:
                break
    out = rf"D:\psp\rom\SO1\work\shot_{member}.png"
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(out)
    print("->", out, len(lines), "lines")


if __name__ == "__main__":
    main()
