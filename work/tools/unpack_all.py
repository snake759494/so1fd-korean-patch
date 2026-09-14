"""Extract every so1pack member to disk, decoding nested SLZ containers fully."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slz
from so1pack import Pack, sig_name

OUT = r"D:\psp\rom\SO1\work\unpack"


def full_decompress(blob: bytes, rec: dict):
    depth = 0
    chain = []
    while slz.is_slz(blob) and depth < 8:
        mode, comp, unp, nxt = slz.parse_header(blob)
        chain.append({"mode": mode, "comp": comp, "unp": unp, "next": nxt})
        try:
            blob = slz.decompress(blob)
        except Exception as e:
            rec["slz_error"] = f"depth{depth}: {e}"
            break
        depth += 1
    if chain:
        rec["slz"] = chain
    return blob


def main():
    p = Pack()
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    for i in range(p.count):
        raw = p.read(i)
        rec = {"idx": i, "off": p.offsets[i], "size": p.sizes[i], "sig": sig_name(raw[:16])}
        data = full_decompress(raw, rec)
        if data is not raw:
            rec["dec_size"] = len(data)
            rec["dec_sig"] = sig_name(data[:16])
        sub = os.path.join(OUT, "%02d" % (i // 500))
        os.makedirs(sub, exist_ok=True)
        with open(os.path.join(sub, "%05d.bin" % i), "wb") as f:
            f.write(data)
        manifest.append(rec)
        if i % 2000 == 0:
            print(i, flush=True)
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f)
    print("done")


if __name__ == "__main__":
    main()
