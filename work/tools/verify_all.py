"""Re-extract text straight from the built so1pack and show what changed."""
from __future__ import annotations

import io
import pickle
import re
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
from expand import expand
import extract2

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
PACK = r"D:\psp\rom\SO1\work\build\so1pack.bin"
SKIP = extract2.SKIP


def main():
    members = [int(a) for a in sys.argv[1:]]
    inv = pickle.load(open(INV, "rb"))
    label = inv.get("label") or inv["canon"]
    is_kana = np.zeros(len(inv["glyphs"]), dtype=bool)
    for g, ch in label.items():
        if ch and 0x3041 <= ord(ch[0]) <= 0x30FF:
            is_kana[g] = True
    p = Pack(PACK)
    for m in members:
        key, count = inv["member_font"][m]
        ids = np.asarray(inv["banks"][key]["ids"], dtype=np.int64)
        leaves = []
        expand(p.read(m), str(m), leaves)
        shown = 0
        print(f"=== member {m}")
        for path, blob in leaves:
            if len(blob) < 8 or SKIP.search(path):
                continue
            for off, indices in extract2.find_runs(blob, count, ids, is_kana,
                                                   "paged", 3):
                s = "".join(label.get(int(ids[i]), "?") for i in indices)
                if any(0xAC00 <= ord(c) <= 0xD7A3 for c in s):
                    print("  ", s)
                    shown += 1
                    if shown >= 22:
                        break
            if shown >= 22:
                break
    p.close()


if __name__ == "__main__":
    main()
