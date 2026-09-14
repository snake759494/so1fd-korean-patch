"""In-place decode safety margin of an SLZ stream.

tri-Ace decompresses SLZ in place: the compressed member sits at the end of
the destination buffer and is consumed as the output is written forward.  The
write pointer must never overtake the read pointer, i.e. at every token

    (bytes written) - (bytes consumed)  <=  unpacked - compressed

Only the final gain is visible in the header, so an encoder that is greedier
early than retail decodes correctly on a PC yet destroys its own input on the
console.  This measures the peak, per member.
"""
from __future__ import annotations

import pickle
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slz
from so1pack import Pack

BUILD = r"D:\psp\rom\SO1\work\build"


def peak_excess(payload: bytes, mode: int, out_size: int, comp: int) -> int:
    """max(written - consumed) - (out_size - comp); <= 0 is safe."""
    src = 0
    made = 0
    flags = 0
    best = -(1 << 30)
    while made < out_size:
        flags >>= 1
        if flags <= 0xFFFF:
            if src >= len(payload):
                break
            flags = 0x00FF0000 | payload[src]
            src += 1
        if flags & 1:
            src += 1
            made += 1
        else:
            if src + 2 > len(payload):
                break
            pos, count = payload[src], payload[src + 1]
            src += 2
            if mode == 2 and count >= 0xF0:
                if count > 0xF0:
                    made += (count & 0x0F) + 3
                else:
                    made += pos + 0x13
                    src += 1
            else:
                made += (count >> 4) + 3
        if made - src > best:
            best = made - src
    return best - (out_size - comp)


def scan(path, members):
    p = Pack() if path is None else Pack(path)
    hist = []
    for m in members:
        blob = p.read(m)
        if not slz.is_slz(blob):
            continue
        try:
            chain = slz.parse_chain(blob)
        except Exception:
            continue
        for mode, comp, unp, _nxt, off in chain:
            if mode not in (1, 2):
                continue
            e = peak_excess(blob[off + 16: off + 16 + comp], mode, unp, comp)
            hist.append((e, m, mode, unp, comp))
    p.close()
    return hist


def main():
    ov = sorted(pickle.load(open(os.path.join(BUILD, "overrides.pkl"), "rb")))
    targets = [("retail", None)]
    for a in sys.argv[1:]:
        targets.append((os.path.basename(a), a))
    for tag, path in targets:
        h = scan(path, ov)
        h.sort(reverse=True)
        over = [x for x in h if x[0] > 16]
        print(f"{tag:22s} slz members {len(h):6d}   excess>16: {len(over):5d}"
              f"   max excess: {h[0][0] if h else 0}")
        for e, m, mode, unp, comp in h[:5]:
            print(f"      member {m:5d} mode{mode} unp={unp:7d} comp={comp:7d} excess={e}")


if __name__ == "__main__":
    main()
