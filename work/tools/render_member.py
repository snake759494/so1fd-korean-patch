"""Render every extracted string of a member with its own font, for reading."""
from __future__ import annotations

import io
import json
import pickle
import sys
import os

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
TSV = r"D:\psp\rom\SO1\work\text.tsv"


def rows_for(member: int, minlen=2):
    out = []
    with io.open(TSV, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 6:
                continue
            if p[0].split("/")[0] == str(member) and int(p[3]) >= minlen:
                out.append(p)
    return out


def main():
    member = int(sys.argv[1])
    minlen = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 45
    inv = pickle.load(open(INV, "rb"))
    key, count = inv["member_font"][member]
    cat = {r["key"]: r for r in json.load(open(r"D:\psp\rom\SO1\work\banks.json"))}
    fi = cat[key]
    leaves = []
    expand(load(member), str(member), leaves)
    d = dict(leaves)
    fb = d[fi["path"]]
    rows = rows_for(member, minlen)
    print("strings:", len(rows))
    os.makedirs(rf"D:\psp\rom\SO1\work\msg\{member}", exist_ok=True)
    index = []
    for page in range((len(rows) + per - 1) // per):
        sel = rows[page * per:(page + 1) * per]
        img = Image.new("L", (760, 15 * len(sel)), 0)
        px = img.load()
        for k, r in enumerate(sel):
            blob = d[r[0]]
            off = int(r[2])
            x, y = 0, k * 15
            n = int(r[3])
            for j in range(n):
                c = blob[off + j * 2] | (blob[off + j * 2 + 1] << 8)
                gi = c - 0x101
                if not (0 <= gi < fi["count"]):
                    continue
                o = fi["bitmaps"] + gi * 24
                for rr in range(12):
                    v = (fb[o + rr * 2] << 8) | fb[o + rr * 2 + 1]
                    for cc in range(12):
                        if (v >> (15 - cc)) & 1 and x + cc < img.width:
                            px[x + cc, y + rr] = 255
                x += max(fb[fi["widths"] + gi], 1)
                if x > 745:
                    break
            index.append({"page": page, "line": k, "path": r[0], "off": off, "len": n})
        img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(
            rf"D:\psp\rom\SO1\work\msg\{member}\p{page:02d}.png")
    json.dump(index, open(rf"D:\psp\rom\SO1\work\msg\{member}\index.json", "w"), indent=1)
    print("pages:", (len(rows) + per - 1) // per)


if __name__ == "__main__":
    main()
