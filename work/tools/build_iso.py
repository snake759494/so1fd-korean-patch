"""Rebuild the SO1 PSP ISO from the original image with a replaced so1pack.bin.

The UMD layout puts so1pack.bin at LBA 55696 and the movies at LBA 482960, so
a same-or-smaller so1pack can be written in place; only its size field in the
directory record changes.  Everything else in the image is byte-preserved.
"""
from __future__ import annotations

import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso, SECTOR

SRC = r"D:\psp\rom\SO1\Star Ocean - First Departure (Japan).iso"


def patch(src: str, dst: str, replacements: dict[str, bytes]):
    """replacements: {'/PSP_GAME/USRDIR/SO1PACK.BIN': data}"""
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    iso = Iso(dst, "r+b")
    entries = {e.path.upper(): e for e in iso.walk()}
    for path, data in replacements.items():
        e = entries[path.upper()]
        limit = e.size
        # how much room until the next file starts
        nxt = min((x.lba for x in entries.values()
                   if not x.is_dir and x.lba > e.lba), default=None)
        room = (nxt - e.lba) * SECTOR if nxt else limit
        if len(data) > room:
            raise ValueError(f"{path}: {len(data)} bytes exceeds {room} of room")
        iso.f.seek(e.lba * SECTOR)
        iso.f.write(data)
        pad = (-len(data)) % SECTOR
        if pad:
            iso.f.write(b"\x00" * pad)
        # update every directory record that describes this file
        for off in e.rec_offsets:
            iso.f.seek(off + 10)
            iso.f.write(struct.pack("<I", len(data)) + struct.pack(">I", len(data)))
        print(f"  {path}: {e.size} -> {len(data)} bytes (room {room})")
    iso.f.flush()
    iso.close()


def main():
    pack = sys.argv[1]
    out = sys.argv[2]
    data = open(pack, "rb").read()
    patch(SRC, out, {"/PSP_GAME/USRDIR/so1pack.bin": data})
    print("wrote", out)


if __name__ == "__main__":
    main()
