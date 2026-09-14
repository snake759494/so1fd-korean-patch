"""so1pack.bin (Star Ocean: First Departure, PSP ULJM05290) container.

Layout, identical to Star Ocean 2 Second Evolution's so2pack.bin:

    u32 file_count
    u32 offset_table_off      (0x10)
    u32 size_table_off
    u32 data_start
    u32 offsets[file_count]   absolute byte offsets, 0x800-aligned
    u32 sizes[file_count]     exact byte sizes

Members are raw payloads; most are SLZ containers.
"""
from __future__ import annotations

import os
import struct
import sys

PACK = r"D:\psp\rom\SO1\work\extract\PSP_GAME\USRDIR\so1pack.bin"
ALIGN = 0x800


class Pack:
    def __init__(self, path=PACK):
        self.path = path
        self.f = open(path, "rb")
        self.size = os.path.getsize(path)
        head = self.f.read(16)
        self.count, self.off_tbl, self.size_tbl, self.data_start = struct.unpack("<4I", head)
        self.f.seek(self.off_tbl)
        self.offsets = list(struct.unpack("<%dI" % self.count, self.f.read(4 * self.count)))
        self.f.seek(self.size_tbl)
        self.sizes = list(struct.unpack("<%dI" % self.count, self.f.read(4 * self.count)))

    def close(self):
        self.f.close()

    def read(self, i: int) -> bytes:
        self.f.seek(self.offsets[i])
        return self.f.read(self.sizes[i])

    def head(self, i: int, n: int = 16) -> bytes:
        self.f.seek(self.offsets[i])
        return self.f.read(min(n, self.sizes[i]))


def sig_name(blob: bytes) -> str:
    if len(blob) < 4:
        return "EMPTY" if not blob else "TINY"
    s4 = blob[:4]
    if s4[:3] == b"SLZ":
        return "SLZ%d" % s4[3]
    for magic in (b"MIG.", b"GIM ", b"RIFF", b"OMG.", b"VAGp", b"PSMF"):
        if s4 == magic[:4]:
            return magic.decode("latin1").strip(". ")
    printable = all(32 <= c < 127 for c in s4)
    if printable:
        return "TXT:" + s4.decode("latin1")
    return "BIN:" + s4.hex().upper()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "survey"
    p = Pack()
    if cmd == "survey":
        from collections import Counter
        c = Counter()
        for i in range(p.count):
            c[sig_name(p.head(i, 16))] += 1
        print(f"count={p.count} off_tbl=0x{p.off_tbl:X} size_tbl=0x{p.size_tbl:X} "
              f"data_start=0x{p.data_start:X} file=0x{p.size:X}")
        print(f"last member ends at 0x{p.offsets[-1] + p.sizes[-1]:X}")
        for k, v in c.most_common(40):
            print(f"  {k:<16} {v}")
    elif cmd == "info":
        i = int(sys.argv[2])
        print(f"idx={i} off=0x{p.offsets[i]:X} size=0x{p.sizes[i]:X} sig={sig_name(p.head(i))}")
        d = p.head(i, 64)
        for j in range(0, len(d), 16):
            row = d[j:j + 16]
            print(f"  {j:04X}  " + " ".join(f"{b:02X}" for b in row).ljust(47) + "  " +
                  "".join(chr(b) if 32 <= b < 127 else "." for b in row))
    p.close()


if __name__ == "__main__":
    main()
