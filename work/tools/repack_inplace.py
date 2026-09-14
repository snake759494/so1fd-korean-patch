"""Patch so1pack.bin in place: keep the retail layout byte-for-byte.

Every rebuilt member has the same length as the original, so members can be
written back at their original offsets.  The offset/size tables, the 0x800
padding and the retail practice of letting identical members share one offset
all stay exactly as shipped - which is what a rebuilt layout put at risk.
"""
from __future__ import annotations

import hashlib
import os
import pickle
import shutil
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack

SRC = r"D:\psp\rom\SO1\work\extract\PSP_GAME\USRDIR\so1pack.bin"
OUT = r"D:\psp\rom\SO1\work\build\so1pack.bin"


def build(overrides: dict[int, bytes], out_path: str = OUT) -> str:
    p = Pack()
    share = defaultdict(list)
    for i in range(p.count):
        share[p.offsets[i]].append(i)

    problems = []
    for m, data in overrides.items():
        if len(data) != p.sizes[m]:
            problems.append(f"member {m}: {len(data)} != original {p.sizes[m]}")
    # a shared offset means writing one member rewrites its twins
    for m in overrides:
        group = [g for g in share[p.offsets[m]] if p.sizes[g]]
        others = [g for g in group if g != m and g not in overrides]
        if others:
            problems.append(f"member {m} shares its offset with unpatched {others}")
    if problems:
        p.close()
        raise ValueError("; ".join(problems[:5]))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    shutil.copyfile(SRC, out_path)
    with open(out_path, "r+b") as f:
        for m, data in sorted(overrides.items()):
            f.seek(p.offsets[m])
            f.write(data)
    p.close()
    return out_path


if __name__ == "__main__":
    ov = pickle.load(open(r"D:\psp\rom\SO1\work\build\overrides.pkl", "rb"))
    path = build(ov)
    print("members written:", len(ov))
    print("size:", os.path.getsize(path), "(original", os.path.getsize(SRC), ")")
