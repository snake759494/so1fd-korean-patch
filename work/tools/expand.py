"""Recursively expand so1pack members: SLZ containers and [count][offsets] archives."""
from __future__ import annotations

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slz

OUT = r"D:\psp\rom\SO1\work\unpack"


def load(i):
    return open(os.path.join(OUT, "%02d" % (i // 500), "%05d.bin" % i), "rb").read()


def as_archive(d: bytes):
    """[u32 count][u32 offsets[count]] with the table itself before offsets[0]."""
    if len(d) < 12:
        return None
    cnt = struct.unpack_from("<I", d, 0)[0]
    if cnt < 1 or cnt > 4096 or 4 + 4 * cnt > len(d):
        return None
    offs = list(struct.unpack_from("<%dI" % cnt, d, 4))
    if offs[0] < 4 + 4 * cnt or offs[0] > len(d):
        return None
    if any(offs[k] > offs[k + 1] for k in range(cnt - 1)):
        return None
    if offs[-1] > len(d):
        return None
    ends = offs[1:] + [len(d)]
    return [(offs[k], ends[k]) for k in range(cnt)]


def as_offset_table(d: bytes):
    """Bare u32 offset table where offsets[0] == table size (tri-Ace style)."""
    if len(d) < 8:
        return None
    first = struct.unpack_from("<I", d, 0)[0]
    if first < 8 or first % 4 or first > len(d) or first > 0x40000:
        return None
    cnt = first // 4
    offs = list(struct.unpack_from("<%dI" % cnt, d, 0))
    if any(offs[k] > offs[k + 1] for k in range(cnt - 1)):
        return None
    if offs[-1] > len(d):
        return None
    ends = offs[1:] + [len(d)]
    return [(offs[k], ends[k]) for k in range(cnt) if ends[k] > offs[k]]


def as_typed_chunks(d: bytes):
    """[u32 count][ (u32 type, u32 offset) * count ] — the field-map container."""
    if len(d) < 12:
        return None
    cnt = struct.unpack_from("<I", d, 0)[0]
    if cnt < 2 or cnt > 64 or 4 + 8 * cnt > len(d):
        return None
    ents = [struct.unpack_from("<2I", d, 4 + 8 * k) for k in range(cnt)]
    if ents[0][1] != 4 + 8 * cnt:
        return None
    offs = [o for _, o in ents]
    if any(offs[k] > offs[k + 1] for k in range(cnt - 1)) or offs[-1] > len(d):
        return None
    if any(t > 64 for t, _ in ents):
        return None
    ends = offs[1:] + [len(d)]
    return [(offs[k], ends[k]) for k in range(cnt)], [t for t, _ in ents]


def expand(d: bytes, path: str, out: list, depth: int = 0, maxdepth: int = 6):
    if depth > maxdepth or not d:
        out.append((path, d))
        return
    if slz.is_slz(d):
        try:
            expand(slz.decompress(d), path + "!", out, depth + 1, maxdepth)
            return
        except Exception:
            pass
    typed = as_typed_chunks(d)
    if typed:
        parts, types = typed
        for k, (a, b) in enumerate(parts):
            expand(d[a:b], f"{path}/t{types[k]}", out, depth + 1, maxdepth)
        return
    parts = as_archive(d)
    if parts is None:
        parts = as_offset_table(d)
    if parts and len(parts) > 1:
        for k, (a, b) in enumerate(parts):
            expand(d[a:b], f"{path}/{k}", out, depth + 1, maxdepth)
        return
    out.append((path, d))


def expand_member(i: int):
    out = []
    expand(load(i), str(i), out)
    return out


if __name__ == "__main__":
    for a in sys.argv[1:]:
        i = int(a)
        leaves = expand_member(i)
        print(f"idx {i}: {len(leaves)} leaves")
        for p, d in leaves[:40]:
            print(f"   {p:<20} {len(d):>9}  {d[:12].hex().upper()}")
