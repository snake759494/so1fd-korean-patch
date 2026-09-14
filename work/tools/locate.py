"""Map expanded leaf paths back to absolute byte ranges inside a member.

Only containers that are plain slices (archives / offset tables / typed
chunks) can be traced; anything under an SLZ node has no direct range.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slz
from expand import as_archive, as_offset_table, as_typed_chunks


def locate(d: bytes, path="", base=0, depth=0, maxdepth=6, out=None):
    if out is None:
        out = {}
    if depth > maxdepth or not d:
        out[path] = (base, base + len(d))
        return out
    if slz.is_slz(d):
        out[path] = (base, base + len(d))          # compressed: children not traceable
        return out
    typed = as_typed_chunks(d)
    if typed:
        parts, types = typed
        for k, (a, b) in enumerate(parts):
            locate(d[a:b], f"{path}/t{types[k]}", base + a, depth + 1, maxdepth, out)
        return out
    parts = as_archive(d) or as_offset_table(d)
    if parts and len(parts) > 1:
        for k, (a, b) in enumerate(parts):
            locate(d[a:b], f"{path}/{k}", base + a, depth + 1, maxdepth, out)
        return out
    out[path] = (base, base + len(d))
    return out


if __name__ == "__main__":
    from expand import load
    for a in sys.argv[1:]:
        m = int(a)
        d = load(m)
        loc = locate(d, str(m))
        print(m, len(d), len(loc), "leaves")
        for k, v in list(loc.items())[:8]:
            print("  ", k, hex(v[0]), hex(v[1]))
