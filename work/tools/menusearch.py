"""Locate the title-menu string table by its shape.

The four entries are
    最初から始める / 途中から始める / ムービーギャラリー / ？？？？？？
so the table contains a run of exactly six identical code units (the ？s) and,
within a short distance, two seven-unit strings sharing their last five units
(から始める).
"""
from __future__ import annotations

import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load


def runs_of(units: np.ndarray, k=6):
    """Start indices of runs of exactly k identical units."""
    n = units.size
    if n < k + 2:
        return []
    same = units[1:] == units[:-1]
    out = []
    i = 0
    while i < same.size:
        if same[i]:
            j = i
            while j < same.size and same[j]:
                j += 1
            length = j - i + 1
            if length == k:
                out.append(i)
            i = j
        else:
            i += 1
    return out


def near_repeat(units: np.ndarray, pos: int, span=120, k=5):
    """True if some k-unit window repeats within +-span of pos."""
    lo = max(0, pos - span)
    hi = min(units.size, pos + span)
    seg = units[lo:hi]
    seen = {}
    for i in range(seg.size - k):
        key = seg[i:i + k].tobytes()
        if key in seen and 5 <= i - seen[key] <= 40:
            if len(set(seg[i:i + k].tolist())) >= 4:
                return lo + seen[key], lo + i
        seen.setdefault(key, i)
    return None


def scan(blob: bytes, label: str):
    hits = []
    for dtype, step, offs in ((np.uint8, 1, (0,)), (np.dtype("<u2"), 2, (0, 1))):
        for off in offs:
            n = (len(blob) - off) // step
            if n < 64:
                continue
            u = np.frombuffer(blob, dtype=dtype, count=n, offset=off)
            for p in runs_of(u, 6):
                v = int(u[p])
                if v in (0, 0xFF, 0xFFFF) or v < 0x20:
                    continue
                nr = near_repeat(u, p)
                if nr:
                    hits.append((step, off, p, v, nr))
                    print(f"  {label} u{step * 8} off={off} run@{p} val=0x{v:X} "
                          f"repeat@{nr}", flush=True)
    return hits


def main():
    ram = r"D:\psp\rom\SO1\work\psp_ram.bin"
    if os.path.exists(ram):
        print("== PSP RAM ==")
        scan(open(ram, "rb").read(), "RAM")
    print("== so1pack ==")
    for i in range(14320):
        try:
            d = load(i)
        except Exception:
            continue
        if len(d) < 128:
            continue
        leaves = []
        try:
            expand(d, str(i), leaves)
        except Exception:
            leaves = [(str(i), d)]
        for p, blob in leaves:
            if len(blob) >= 128:
                scan(blob, p)


if __name__ == "__main__":
    main()
