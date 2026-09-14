"""Verify a rebuilt so1pack.bin exposes byte-identical members (except overrides)."""
from __future__ import annotations

import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack


def main():
    new = sys.argv[1]
    a = Pack()
    b = Pack(new)
    assert a.count == b.count, (a.count, b.count)
    bad = 0
    changed = []
    for i in range(a.count):
        da, db = a.read(i), b.read(i)
        if da != db:
            changed.append((i, len(da), len(db)))
            bad += 1
    a.close()
    b.close()
    print(f"members {a.count}; differing {bad}")
    for i, la, lb in changed[:40]:
        print(f"  idx {i}: {la} -> {lb}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
