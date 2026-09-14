import json
import os
import sys
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slz
from so1pack import sig_name

OUT = r"D:\psp\rom\SO1\work\unpack"


def load(i):
    return open(os.path.join(OUT, "%02d" % (i // 500), "%05d.bin" % i), "rb").read()


def dump(d, off=0, n=128, indent="  "):
    d = d[off:off + n]
    for j in range(0, len(d), 16):
        row = d[j:j + 16]
        print(f"{indent}{off + j:06X}  " + " ".join(f"{b:02X}" for b in row).ljust(47) + "  " +
              "".join(chr(b) if 32 <= b < 127 else "." for b in row))


def try_subarchive(d):
    """If d looks like [u32 hdr_size][u32 offsets...], report the entries."""
    if len(d) < 8:
        return None
    hdr = struct.unpack_from("<I", d, 0)[0]
    if hdr < 8 or hdr > len(d) or hdr % 4:
        return None
    cnt = hdr // 4
    offs = list(struct.unpack_from("<%dI" % cnt, d, 0))
    if offs[0] != hdr:
        return None
    if any(offs[k] > offs[k + 1] for k in range(cnt - 1)):
        return None
    if offs[-1] > len(d):
        return None
    return offs


def main():
    for i in [int(x) for x in sys.argv[1:]]:
        d = load(i)
        print(f"=== idx {i}  len={len(d)}  sig={sig_name(d[:16])}")
        offs = try_subarchive(d)
        if offs:
            print(f"  subarchive: {len(offs)} offsets, last=0x{offs[-1]:X}")
            for k in range(len(offs)):
                a = offs[k]
                b = offs[k + 1] if k + 1 < len(offs) else len(d)
                sub = d[a:b]
                print(f"   [{k}] 0x{a:06X}..0x{b:06X} ({b - a:>8}) {sig_name(sub[:16])}"
                      + (f"  -> unp={slz.parse_header(sub)[2]}" if slz.is_slz(sub) else ""))
                if k > 40:
                    print("   ...")
                    break
        else:
            dump(d, 0, 128)


if __name__ == "__main__":
    main()
