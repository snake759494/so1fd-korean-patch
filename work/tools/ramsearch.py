"""Search a live PPSSPP process's memory for a known glyph bitmap.

Byte-aligned candidates first; then a bit-level sweep over row strides so a
non-byte-aligned packing (12 bits per row) is still found.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import sys
import os

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from find_font import glyph_bits, patterns

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class MEMORY_BASIC_INFORMATION64(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_ulonglong),
                ("AllocationBase", ctypes.c_ulonglong),
                ("AllocationProtect", wt.DWORD),
                ("__alignment1", wt.DWORD),
                ("RegionSize", ctypes.c_ulonglong),
                ("State", wt.DWORD),
                ("Protect", wt.DWORD),
                ("Type", wt.DWORD),
                ("__alignment2", wt.DWORD)]


MEM_COMMIT = 0x1000
READABLE = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}   # PAGE_READONLY..EXECUTE_WRITECOPY
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01


def regions(h):
    addr = 0
    mbi = MEMORY_BASIC_INFORMATION64()
    while addr < 0x7FFFFFFFFFFF:
        r = k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not r:
            break
        base, size = mbi.BaseAddress, mbi.RegionSize
        if size == 0:
            break
        prot = mbi.Protect & 0xFF
        if mbi.State == MEM_COMMIT and prot in READABLE and not (mbi.Protect & PAGE_GUARD):
            yield base, size
        addr = base + size


def read(h, base, size):
    buf = (ctypes.c_char * size)()
    n = ctypes.c_size_t(0)
    if not k32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(n)):
        return None
    return bytes(buf[:n.value])


def bit_rows(blob: bytes, msb=True):
    a = np.frombuffer(blob, dtype=np.uint8)
    bits = np.unpackbits(a, bitorder="big" if msb else "little")
    return bits


def bit_search(blob, bits12, strides):
    """Find the 12-row glyph at any bit offset for the given bit strides."""
    b = bit_rows(blob, True).astype(np.int8)
    n = b.size
    hits = []
    # 12-bit value at every bit position
    val = np.zeros(n, dtype=np.int32)
    for k in range(12):
        val[:n - k] |= (b[k:].astype(np.int32) << (11 - k))
    rows = [int("".join("1" if v else "0" for v in r), 2) for r in bits12]
    # pick two distinctive rows to prefilter
    order = sorted(range(12), key=lambda i: -bin(rows[i]).count("1"))
    a0, a1 = order[0], order[1]
    for S in strides:
        limit = n - 12 * S - 12
        if limit <= 0:
            continue
        cand = np.flatnonzero(val[:limit] == rows[0])
        if cand.size == 0:
            continue
        ok = cand
        for r in (a0, a1, 5, 8):
            ok = ok[val[ok + r * S] == rows[r]]
            if ok.size == 0:
                break
        for p in ok[:5]:
            if all(val[p + i * S] == rows[i] for i in range(12)):
                hits.append((S, int(p)))
    return hits


def main():
    pid = int(sys.argv[1])
    bits = glyph_bits(0, 40)
    pats = patterns(bits)
    frags = {k: v[2 * (len(v) // 12): 10 * (len(v) // 12)] for k, v in pats.items()}
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        print("OpenProcess failed", ctypes.get_last_error())
        return 1
    total = 0
    found = []
    for base, size in regions(h):
        if size > 1 << 30:
            continue
        blob = read(h, base, size)
        if not blob:
            continue
        total += len(blob)
        for name, frag in frags.items():
            p = blob.find(frag)
            while p >= 0:
                found.append((name, hex(base + p), base, size))
                print("BYTE HIT", name, hex(base + p), "region", hex(base), size, flush=True)
                p = blob.find(frag, p + 1)
    print("scanned", total, "bytes;", len(found), "byte hits")
    if not found:
        print("bit-level sweep ...")
        for base, size in regions(h):
            if size > 1 << 28:
                continue
            blob = read(h, base, size)
            if not blob or len(blob) < 4096:
                continue
            hs = bit_search(blob, bits, [12, 16, 18, 24, 32, 96, 128, 144, 192, 256, 512, 1024, 2048, 4096])
            for S, p in hs:
                print("BIT HIT stride", S, "at", hex(base + p // 8), "bitoff", p % 8,
                      "region", hex(base), size, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
