"""Star Ocean: First Departure text-bank container.

Layout (member 10 is the canonical example):

    u16 id, u16 offset   x N          message index, terminated by 0xFFFF
    <message data>                    2-byte glyph codes, 0x0000 terminates
    u32 num_glyphs                    (font subset used by this bank)
    u32 glyph_height                  always 12
    u8  width[num_glyphs]             advance width per glyph
    u8  bitmap[num_glyphs][24]        12 rows x 2 bytes, MSB-first, 12 px wide

Glyph code C addresses glyph index C - 0x20 (code 0x20 == the blank glyph).
"""
from __future__ import annotations

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GLYPH_BYTES = 24
CODE_BASE = 0x20


def parse_index(d: bytes, base: int = 0):
    ents = []
    off = base
    while off + 4 <= len(d):
        cid, coff = struct.unpack_from("<2H", d, off)
        if cid == 0xFFFF:
            off += 2
            break
        if coff < off or coff > len(d):
            return None, None
        ents.append((cid, coff))
        off += 4
    if not ents or off > len(d):
        return None, None
    return ents, off


def find_font(d: bytes, data_start: int):
    """Locate (num_glyphs, height, widths_off, bitmap_off) after the messages."""
    end = max(o for _, o in _last_index_cache) if False else None
    return None


def parse(d: bytes):
    ents, data_start = parse_index(d)
    if not ents:
        return None
    hi = max(o for _, o in ents)
    # message data runs to the terminator of the last record
    p = hi
    while p + 2 <= len(d) and struct.unpack_from("<H", d, p)[0] != 0:
        p += 2
    p += 2                                     # skip terminator
    # font header is 4-byte aligned right after the message block
    for pad in range(0, 8, 2):
        q = p + pad
        if q + 8 > len(d):
            break
        n, h = struct.unpack_from("<2I", d, q)
        if h == 12 and 0 < n < 20000 and q + 8 + n + n * GLYPH_BYTES <= len(d) + 64:
            wid = q + 8
            bmp = wid + n
            return {"index": ents, "data_start": data_start, "msg_end": p,
                    "font_hdr": q, "num_glyphs": n, "height": h,
                    "widths": wid, "bitmaps": bmp}
    return {"index": ents, "data_start": data_start, "msg_end": p, "font_hdr": None}


def messages(d: bytes, info: dict):
    """Return {id: [codes]} decoded from the index."""
    out = {}
    for cid, off in info["index"]:
        codes = []
        p = off
        while p + 2 <= len(d):
            v = struct.unpack_from("<H", d, p)[0]
            p += 2
            if v == 0:
                break
            codes.append(v)
        out[cid] = codes
    return out


def glyph(d: bytes, info: dict, index: int):
    o = info["bitmaps"] + index * GLYPH_BYTES
    rows = []
    for y in range(12):
        hi, lo = d[o + y * 2], d[o + y * 2 + 1]
        v = (hi << 8) | lo
        rows.append([(v >> (15 - x)) & 1 for x in range(12)])
    return rows


if __name__ == "__main__":
    from expand import load
    for a in sys.argv[1:]:
        d = load(int(a))
        info = parse(d)
        if not info:
            print(a, "not a text bank")
            continue
        print(f"idx {a}: msgs={len(info['index'])} data=0x{info['data_start']:X} "
              f"msg_end=0x{info['msg_end']:X} font_hdr={info['font_hdr'] and hex(info['font_hdr'])} "
              f"glyphs={info.get('num_glyphs')} widths=0x{info.get('widths', 0):X} "
              f"bitmaps=0x{info.get('bitmaps', 0):X} len=0x{len(d):X}")
