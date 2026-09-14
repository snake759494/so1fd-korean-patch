"""Dump PPSSPP's emulated PSP RAM by locating the big contiguous mapping."""
from __future__ import annotations

import ctypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ramsearch import k32, regions, read, PROCESS_QUERY_INFORMATION, PROCESS_VM_READ


def main():
    pid = int(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else r"D:\psp\rom\SO1\work\psp_ram.bin"
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        print("OpenProcess failed", ctypes.get_last_error())
        return 1
    boot = open(r"D:\psp\rom\SO1\work\extract\PSP_GAME\SYSDIR\BOOT.BIN", "rb").read()
    needle = boot[0x400:0x480]
    cands = []
    for base, size in regions(h):
        if size < (8 << 20) or size > (1 << 30):
            continue
        blob = read(h, base, size)
        if not blob:
            continue
        p = blob.find(needle)
        if p >= 0:
            print(f"found BOOT text at region 0x{base:X} (+0x{p:X}) size 0x{size:X}")
            cands.append((base, size, p, blob))
    if not cands:
        print("no candidate RAM region found")
        return 2
    base, size, p, blob = max(cands, key=lambda c: c[1])
    with open(out, "wb") as f:
        f.write(blob)
    print(f"wrote {out} ({len(blob)} bytes); BOOT text at file offset 0x{p - 0x400:X}")
    print(f"=> PSP virtual base likely 0x08800000 at file offset 0x{(p - 0x400) - 0x4000:X}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
