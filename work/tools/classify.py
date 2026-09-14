"""Group unpacked members by leading signature and show one sample of each."""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import sig_name

OUT = r"D:\psp\rom\SO1\work\unpack"


def load(i):
    return open(os.path.join(OUT, "%02d" % (i // 500), "%05d.bin" % i), "rb").read()


def main():
    manifest = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    groups = defaultdict(list)
    for rec in manifest:
        i = rec["idx"]
        d = load(i)
        groups[sig_name(d[:16])].append((i, len(d)))
    order = sorted(groups.items(), key=lambda kv: -sum(s for _, s in kv[1]))
    for sig, members in order[:40]:
        total = sum(s for _, s in members)
        i0 = members[0][0]
        d = load(i0)[:48]
        hexs = " ".join(f"{b:02X}" for b in d)
        idxs = ",".join(str(m[0]) for m in members[:8])
        print(f"{sig:<16} n={len(members):<6} bytes={total:<12} idx[{idxs}]")
        print(f"                 {hexs}")


if __name__ == "__main__":
    main()
