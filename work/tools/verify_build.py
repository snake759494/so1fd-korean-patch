"""Structural check of the built so1pack: every patched member must still
parse, expose the same font block, and render Hangul where we wrote it."""
from __future__ import annotations

import json
import pickle
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
from expand import expand
from fieldbank import fonts
import kfont

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"
PACK = r"D:\psp\rom\SO1\work\build\so1pack.bin"
BUILD = r"D:\psp\rom\SO1\work\build"


def main():
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    ov = pickle.load(open(os.path.join(BUILD, "overrides.pkl"), "rb"))
    p = Pack(PACK)
    # a reference set of Hangul bitmaps to prove the font really got Korean
    font = kfont._font()
    ref = {kfont.encode(kfont.render(c, font)) for c in "가나다라마소지금전투오의"}
    ok = bad = hangul = 0
    problems = []
    for m in sorted(ov):
        key, count = inv["member_font"][m]
        fi = cat[key]
        try:
            leaves = []
            raw = p.read(m)
            expand(raw, str(m), leaves)
            d = dict(leaves)
            # a stored member may still be SLZ-wrapped; catalogue paths were
            # made from the decompressed view, so strip the leading shells
            if fi["path"] not in d:
                pre = str(m)
                for k in range(1, 5):
                    alt = pre + "!" * k + fi["path"][len(pre):]
                    if alt in d:
                        d[fi["path"]] = d[alt]
                        break
            blob = d.get(fi["path"])
            if blob is None:
                problems.append((m, "font leaf missing"))
                bad += 1
                continue
            fs = fonts(blob)
            if not any(f["count"] == count for f in fs):
                problems.append((m, f"font count changed: {[f['count'] for f in fs]}"))
                bad += 1
                continue
            f = max(fs, key=lambda x: x["count"])
            bm = blob[f["bitmaps"]:f["bitmaps"] + f["count"] * 24]
            found = any(bm[i * 24:(i + 1) * 24] in ref for i in range(f["count"]))
            hangul += bool(found)
            ok += 1
        except Exception as e:
            problems.append((m, f"parse error: {e}"))
            bad += 1
    p.close()
    print(f"patched members {len(ov)}: structurally ok {ok}, broken {bad}")
    print(f"members whose font contains reference Hangul glyphs: {hangul}")
    for m, msg in problems[:20]:
        print("  ", m, msg)


if __name__ == "__main__":
    main()
