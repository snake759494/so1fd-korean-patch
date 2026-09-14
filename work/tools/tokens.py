"""Census of the token forms the retail SLZ streams actually use.

Our encoders are reconstructions: a roundtrip through our own decoder proves
nothing about token forms the real engine never emits.  This walks retail
payloads and tallies, per mode, which match-length nibbles and which RLE
escapes appear - anything we emit but retail never does is a red flag.
"""
from __future__ import annotations

import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slz
from so1pack import Pack


def walk(payload: bytes, mode: int, out_size: int, tally: Counter):
    """Same control flow as decompress_payload, tallying token shapes."""
    src = 0
    made = 0
    flags = 0
    while made < out_size:
        flags >>= 1
        if flags <= 0xFFFF:
            if src >= len(payload):
                return
            flags = 0x00FF0000 | payload[src]
            src += 1
        if flags & 1:
            tally[(mode, "lit")] += 1
            src += 1
            made += 1
        else:
            if src + 2 > len(payload):
                return
            pos, count = payload[src], payload[src + 1]
            src += 2
            if mode == 2 and count >= 0xF0:
                if count > 0xF0:
                    n = (count & 0x0F) + 3
                    tally[(mode, "rle_short")] += 1
                else:
                    n = pos + 0x13
                    src += 1
                    tally[(mode, "rle_long")] += 1
                made += n
            else:
                nib = count >> 4
                tally[(mode, "match_nib", nib)] += 1
                made += nib + 3
    return


def main():
    p = Pack()
    tally = Counter()
    seen = Counter()
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    step = max(1, p.count // limit)
    for m in range(0, p.count, step):
        try:
            blob = p.read(m)
        except Exception:
            continue
        if not slz.is_slz(blob):
            continue
        try:
            chain = slz.parse_chain(blob)
        except Exception:
            continue
        for mode, comp, unp, _nxt, off in chain:
            if mode not in (1, 2):
                continue
            seen[mode] += 1
            walk(blob[off + 16: off + 16 + comp], mode, unp, tally)
    p.close()
    print("members scanned:", limit, " slz members by mode:", dict(seen))
    for mode in (1, 2):
        print(f"--- mode {mode}")
        lit = tally[(mode, "lit")]
        print(f"    literals   : {lit:,}")
        for nib in range(16):
            c = tally[(mode, "match_nib", nib)]
            if c:
                print(f"    match len {nib + 3:>2} (nibble {nib:X}) : {c:,}")
        for k in ("rle_short", "rle_long"):
            if tally[(mode, k)]:
                print(f"    {k:<10}: {tally[(mode, k)]:,}")


if __name__ == "__main__":
    main()
