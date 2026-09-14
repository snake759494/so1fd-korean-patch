"""Confirm the built ISO differs from the original only inside so1pack.bin."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso, SECTOR

SRC = r"D:\psp\rom\SO1\Star Ocean - First Departure (Japan).iso"
OUT = r"D:\psp\rom\SO1\work\build\SO1_Korean.iso"
CHUNK = 1 << 22


def main():
    iso = Iso(SRC)
    e = iso.find("/PSP_GAME/USRDIR/so1pack.bin")
    iso.close()
    lo = e.lba * SECTOR
    hi = lo + e.size
    print(f"so1pack range: 0x{lo:X}..0x{hi:X} ({e.size} bytes)")
    a = open(SRC, "rb")
    b = open(OUT, "rb")
    if os.path.getsize(SRC) != os.path.getsize(OUT):
        print(f"SIZE DIFFERS: {os.path.getsize(SRC)} vs {os.path.getsize(OUT)}")
    pos = 0
    outside = 0
    inside = 0
    first_out = None
    while True:
        x = a.read(CHUNK)
        y = b.read(CHUNK)
        if not x and not y:
            break
        n = min(len(x), len(y))
        for i in range(n):
            if x[i] != y[i]:
                off = pos + i
                if lo <= off < hi:
                    inside += 1
                else:
                    outside += 1
                    if first_out is None:
                        first_out = off
        pos += n
    a.close()
    b.close()
    print(f"differing bytes inside so1pack : {inside}")
    print(f"differing bytes outside        : {outside}"
          + (f" (first at 0x{first_out:X})" if first_out is not None else ""))
    return 0 if outside == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
