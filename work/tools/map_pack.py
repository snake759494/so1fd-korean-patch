"""Run-length map of member signatures across the pack index space."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import sig_name

OUT = r"D:\psp\rom\SO1\work\unpack"


def load(i):
    return open(os.path.join(OUT, "%02d" % (i // 500), "%05d.bin" % i), "rb").read()


def main():
    manifest = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    sigs = []
    sizes = []
    for rec in manifest:
        d = load(rec["idx"])
        sigs.append(sig_name(d[:16]) if d else "EMPTY")
        sizes.append(len(d))
    runs = []
    start = 0
    for i in range(1, len(sigs) + 1):
        if i == len(sigs) or sigs[i] != sigs[start]:
            runs.append((start, i - 1, sigs[start], sum(sizes[start:i])))
            start = i
    print("runs:", len(runs))
    for a, b, s, tot in runs:
        if b - a >= 2 or tot > 200000:
            print(f"  {a:>5}-{b:<5} n={b - a + 1:<5} {s:<16} bytes={tot}")
    json.dump({"sigs": sigs, "sizes": sizes}, open(r"D:\psp\rom\SO1\work\sigmap.json", "w"))


if __name__ == "__main__":
    main()
