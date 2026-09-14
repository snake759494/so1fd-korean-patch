"""Find glyph-coded strings by their repeat fingerprint.

"ムービーギャラリー" (movie gallery, on the title menu) is 9 characters with
'ー' at positions 1, 3 and 8 and seven distinct others -- a fingerprint that
survives any unknown encoding as long as one code unit == one character.
"""
from __future__ import annotations

import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load


def fingerprint(s: str):
    """Return (length, groups) where groups lists index sets of equal chars."""
    idx = {}
    for i, c in enumerate(s):
        idx.setdefault(c, []).append(i)
    return len(s), list(idx.values())


def match(units: np.ndarray, length: int, groups):
    n = units.size - length
    if n <= 0:
        return []
    cand = np.arange(n, dtype=np.int64)
    for g in groups:
        if len(g) > 1:
            for k in g[1:]:
                cand = cand[units[cand + g[0]] == units[cand + k]]
                if cand.size == 0:
                    return []
    reps = [g[0] for g in groups]
    for a in range(len(reps)):
        for b in range(a + 1, len(reps)):
            cand = cand[units[cand + reps[a]] != units[cand + reps[b]]]
            if cand.size == 0:
                return []
    return cand.tolist()


def scan_blob(blob: bytes, length, groups, label, limit=6):
    a = np.frombuffer(blob, dtype=np.uint8)
    for p in match(a, length, groups)[:limit]:
        print(f"  U8  {label} @0x{p:X}: {blob[p:p + length].hex()}", flush=True)
    for off in (0, 1):
        n = (len(blob) - off) // 2
        if n <= length:
            continue
        u = np.frombuffer(blob, dtype="<u2", count=n, offset=off)
        for p in match(u, length, groups)[:limit]:
            q = off + p * 2
            print(f"  U16 {label} @0x{q:X}: {blob[q:q + length * 2].hex()}", flush=True)


def main():
    word = sys.argv[1] if len(sys.argv) > 1 else "ムービーギャラリー"
    length, groups = fingerprint(word)
    print(f"pattern '{word}' len={length} groups={groups}")
    ram = r"D:\psp\rom\SO1\work\psp_ram.bin"
    if os.path.exists(ram):
        print("== PSP RAM ==")
        scan_blob(open(ram, "rb").read(), length, groups, "RAM", limit=20)
    print("== so1pack ==")
    for i in range(14320):
        try:
            d = load(i)
        except Exception:
            continue
        if len(d) < 64:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            if len(blob) >= 64:
                scan_blob(blob, length, groups, p, limit=2)


if __name__ == "__main__":
    main()
