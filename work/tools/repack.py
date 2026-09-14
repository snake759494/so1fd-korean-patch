"""Rebuild so1pack.bin from the original plus a set of replaced members.

Members keep their original order; each starts on a 0x800 boundary.  A member
supplied in `overrides` replaces the original *raw* (still SLZ-wrapped where it
was) payload, so callers must re-wrap compressed members themselves.
"""
from __future__ import annotations

import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack, ALIGN

OUT = r"D:\psp\rom\SO1\work\build\so1pack.bin"


def build(overrides: dict[int, bytes], out_path: str = OUT) -> str:
    p = Pack()
    count = p.count
    off_tbl = 0x10
    size_tbl = off_tbl + 4 * count
    data_start = (size_tbl + 4 * count + ALIGN - 1) // ALIGN * ALIGN
    offsets = [0] * count
    sizes = [0] * count
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    seen: dict[bytes, int] = {}
    with open(out_path, "wb") as f:
        f.write(b"\x00" * data_start)
        cur = data_start
        for i in range(count):
            data = overrides.get(i)
            if data is None:
                data = p.read(i)
            sizes[i] = len(data)
            key = hashlib.sha256(data).digest() + len(data).to_bytes(8, "little")
            if key in seen:                      # the retail pack shares identical members
                offsets[i] = seen[key]
                continue
            offsets[i] = cur
            seen[key] = cur
            f.write(data)
            pad = (-len(data)) % ALIGN
            if pad:
                f.write(b"\x00" * pad)
            cur += len(data) + pad
        f.seek(0)
        f.write(struct.pack("<4I", count, off_tbl, size_tbl, data_start))
        f.seek(off_tbl)
        f.write(struct.pack("<%dI" % count, *offsets))
        f.seek(size_tbl)
        f.write(struct.pack("<%dI" % count, *sizes))
    p.close()
    return out_path


if __name__ == "__main__":
    import hashlib
    path = build({}, sys.argv[1] if len(sys.argv) > 1 else OUT)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    orig = hashlib.sha256(open(
        r"D:\psp\rom\SO1\work\extract\PSP_GAME\USRDIR\so1pack.bin", "rb").read()).hexdigest()
    print("rebuilt:", h)
    print("original:", orig)
    print("identical" if h == orig else "DIFFERENT")
