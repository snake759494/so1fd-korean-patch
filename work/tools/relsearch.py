"""Relative (delta) search for glyph-coded Latin text.

The game draws "Original version developed by tri-Ace Inc." on the title
screen but stores no ASCII, so the codes are glyph indices.  If Latin glyphs
are numbered in ASCII order, the consecutive differences of the codes equal
the consecutive differences of the ASCII string -- searchable without knowing
the offset.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import expand, load

WORDS = ["developed", "Reserved", "Original", "version", "Rights", "SQUARE"]


def deltas(s: str):
    return np.array([ord(s[i + 1]) - ord(s[i]) for i in range(len(s) - 1)], dtype=np.int64)


def find_u8(a: np.ndarray, d: np.ndarray):
    if a.size < d.size + 1:
        return []
    diff = (a[1:].astype(np.int64) - a[:-1].astype(np.int64))
    return _match(diff, d)


def find_u16(blob: bytes, d: np.ndarray, off: int):
    n = (len(blob) - off) // 2
    if n < d.size + 1:
        return []
    a = np.frombuffer(blob, dtype="<u2", count=n, offset=off).astype(np.int64)
    diff = a[1:] - a[:-1]
    return [p * 2 + off for p in _match(diff, d)]


def _match(diff: np.ndarray, d: np.ndarray):
    ok = diff[: diff.size - d.size + 1] == d[0]
    idx = np.flatnonzero(ok)
    for k in range(1, d.size):
        if idx.size == 0:
            return []
        idx = idx[diff[idx + k] == d[k]]
    return idx.tolist()


def main():
    pats = [(w, deltas(w)) for w in WORDS]
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
            if len(blob) < 64:
                continue
            a = np.frombuffer(blob, dtype=np.uint8)
            for w, dd in pats:
                for q in find_u8(a, dd)[:3]:
                    print(f"U8  {p} @0x{q:X} '{w}' base={blob[q] - ord(w[0])}", flush=True)
                for off in (0, 1):
                    for q in find_u16(blob, dd, off)[:3]:
                        v = int(np.frombuffer(blob, dtype="<u2", count=1, offset=q)[0])
                        print(f"U16 {p} @0x{q:X} '{w}' base={v - ord(w[0])}", flush=True)
        if i % 1000 == 0:
            print("..", i, flush=True)


if __name__ == "__main__":
    main()
