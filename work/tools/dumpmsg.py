"""Dump a message leaf as text + control bytes."""
from __future__ import annotations

import json
import pickle
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"


def main():
    member = int(sys.argv[1])
    want = sys.argv[2] if len(sys.argv) > 2 else None
    inv = pickle.load(open(INV, "rb"))
    key, count = inv["member_font"][member]
    ids = inv["banks"][key]["ids"]
    label = inv["canon"]
    leaves = []
    expand(load(member), str(member), leaves)
    for p, blob in leaves:
        if want and p != want:
            continue
        if len(blob) > 4096:
            continue
        print(f"=== {p} ({len(blob)} bytes)")
        i = 0
        line = []
        while i < len(blob):
            if i + 1 < len(blob):
                c = blob[i] | (blob[i + 1] << 8)
                if 0x101 <= c < 0x101 + count:
                    g = ids[c - 0x101]
                    line.append(label.get(g, "\ue000"))
                    i += 2
                    continue
            line.append("<%02X>" % blob[i])
            i += 1
        print("".join(line).replace("\ue000", "?"))
        print()


if __name__ == "__main__":
    main()
