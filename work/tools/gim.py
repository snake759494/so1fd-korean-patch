"""GIM ("MIG.00.1PSP") reader/writer for the PSP Star Ocean textures.

Chunk header (16 bytes): u16 type, u16 pad, u32 size, u32 next, u32 data_off.
Image/palette header (0x30 bytes): u16 hdr_size, u16 pad, u16 format, u16 order,
u16 width, u16 height, u16 bpp, u16 pitch_align, u16 h_align, u16 pad2,
u32 pad3, u32 pixels_rel, u32 pixels_end.
"""
from __future__ import annotations

import struct
import sys

FMT_NAMES = {0: "RGBA5650", 1: "RGBA5551", 2: "RGBA4444", 3: "RGBA8888",
             4: "INDEX4", 5: "INDEX8", 6: "INDEX16", 7: "INDEX32"}
BPP = {0: 16, 1: 16, 2: 16, 3: 32, 4: 4, 5: 8, 6: 16, 7: 32}


def _blocks(data: bytes):
    """Walk the chunk tree, yielding (type, chunk_off, size, data_off)."""
    out = []

    def walk(off, end):
        while off + 16 <= end:
            typ, _pad, size, nxt, doff = struct.unpack_from("<HHIII", data, off)
            if size < 16 or off + size > len(data):
                break
            out.append((typ, off, size, off + doff))
            if typ in (0x02, 0x03):
                walk(off + doff, off + size)
            off += size
    walk(0x10, len(data))
    return out


def _img_header(data, h):
    (hdr, _p, fmt, order, w, hh, bpp, pa, ha, _p2) = struct.unpack_from("<10H", data, h)
    pix_rel, pix_end = struct.unpack_from("<2I", data, h + 0x18)
    return {"hdr": hdr, "fmt": fmt, "fmt_name": FMT_NAMES.get(fmt, str(fmt)),
            "order": order, "w": w, "h": hh, "bpp": bpp,
            "pitch_align": pa, "h_align": ha,
            "pix": h + pix_rel, "pix_end": h + pix_end, "hdr_off": h}


def parse(data: bytes):
    if data[:12] != b"MIG.00.1PSP\x00":
        raise ValueError("not GIM")
    imgs, pals = [], []
    for typ, off, size, doff in _blocks(data):
        if typ == 0x04:
            imgs.append(_img_header(data, doff))
        elif typ == 0x05:
            pals.append(_img_header(data, doff))
    return imgs, pals


# --- PSP swizzle ------------------------------------------------------------

def unswizzle(buf: bytes, width_bytes: int, height: int) -> bytes:
    out = bytearray(len(buf))
    bw = width_bytes // 16
    bh = height // 8
    src = 0
    for by in range(bh):
        for bx in range(bw):
            for y in range(8):
                d = (by * 8 + y) * width_bytes + bx * 16
                out[d:d + 16] = buf[src:src + 16]
                src += 16
    return bytes(out)


def swizzle(buf: bytes, width_bytes: int, height: int) -> bytes:
    out = bytearray(len(buf))
    bw = width_bytes // 16
    bh = height // 8
    dst = 0
    for by in range(bh):
        for bx in range(bw):
            for y in range(8):
                s = (by * 8 + y) * width_bytes + bx * 16
                out[dst:dst + 16] = buf[s:s + 16]
                dst += 16
    return bytes(out)


def _align(v, a):
    return (v + a - 1) // a * a


def decode_palette(data, p):
    n = p["w"] * p["h"]
    off = p["pix"]
    cols = []
    if p["fmt"] == 3:
        for i in range(n):
            r, g, b, a = data[off + i * 4: off + i * 4 + 4]
            cols.append((r, g, b, min(255, a * 2) if a <= 128 else 255))
    elif p["fmt"] == 1:
        for i in range(n):
            v = struct.unpack_from("<H", data, off + i * 2)[0]
            r = (v & 31) * 255 // 31
            g = ((v >> 5) & 31) * 255 // 31
            b = ((v >> 10) & 31) * 255 // 31
            a = 255 if (v >> 15) else 0
            cols.append((r, g, b, a))
    elif p["fmt"] == 2:
        for i in range(n):
            v = struct.unpack_from("<H", data, off + i * 2)[0]
            r = (v & 15) * 17
            g = ((v >> 4) & 15) * 17
            b = ((v >> 8) & 15) * 17
            a = ((v >> 12) & 15) * 17
            cols.append((r, g, b, a))
    else:
        raise ValueError("palette fmt %d" % p["fmt"])
    return cols


def indices(data, im):
    """Return a w*h list of palette indices (INDEX4/INDEX8 only)."""
    bpp = BPP[im["fmt"]]
    row_bytes = im["w"] * bpp // 8
    pitch = _align(row_bytes, im["pitch_align"])
    height = _align(im["h"], im["h_align"])
    raw = data[im["pix"]: im["pix"] + pitch * height]
    if im["order"] == 1:
        raw = unswizzle(raw, pitch, height)
    out = []
    for y in range(im["h"]):
        row = raw[y * pitch: y * pitch + row_bytes]
        if bpp == 8:
            out.extend(row)
        elif bpp == 4:
            for b in row:
                out.append(b & 0x0F)
                out.append(b >> 4)
        else:
            raise ValueError("bpp %d" % bpp)
    return out[:im["w"] * im["h"]] if bpp == 8 else out


def to_image(data: bytes):
    from PIL import Image
    imgs, pals = parse(data)
    if not imgs:
        return None
    im = imgs[0]
    if im["fmt"] in (4, 5):
        if not pals:
            return None
        cols = decode_palette(data, pals[0])
        idx = indices(data, im)
        img = Image.new("RGBA", (im["w"], im["h"]))
        px = img.load()
        w = im["w"]
        for i, v in enumerate(idx[:w * im["h"]]):
            px[i % w, i // w] = cols[v] if v < len(cols) else (0, 0, 0, 0)
        return img
    return None


def main():
    import os
    OUT = r"D:\psp\rom\SO1\work\unpack"
    for a in sys.argv[1:]:
        i = int(a)
        d = open(os.path.join(OUT, "%02d" % (i // 500), "%05d.bin" % i), "rb").read()
        try:
            imgs, pals = parse(d)
        except Exception as e:
            print(i, "ERR", e)
            continue
        print(f"idx {i}: len={len(d)}")
        for b in imgs:
            print(f"   IMG {b['fmt_name']:<9} {b['w']}x{b['h']} bpp={b['bpp']} "
                  f"order={b['order']} pix=0x{b['pix']:X}")
        for b in pals:
            print(f"   PAL {b['fmt_name']:<9} {b['w']}x{b['h']} bpp={b['bpp']} pix=0x{b['pix']:X}")


if __name__ == "__main__":
    main()
