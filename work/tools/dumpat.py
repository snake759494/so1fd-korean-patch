"""Side-by-side bytes of one leaf region, retail vs build."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
import tree


def leaf(pack, member, path):
    root = tree.parse(pack.read(member), str(member))
    for n in tree.walk(root):
        if n.path == path and n.data and not n.kids:
            return n.data
    return None


def main():
    member = int(sys.argv[1])
    path = sys.argv[2]
    off = int(sys.argv[3])
    span = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    build = sys.argv[5] if len(sys.argv) > 5 else r"D:\psp\rom\SO1\work\build\so1pack_v08.bin"
    a = Pack()
    b = Pack(build)
    da = leaf(a, member, path)
    db = leaf(b, member, path)
    a.close()
    b.close()
    if da is None or db is None:
        print("leaf not found", da is None, db is None)
        return
    lo = max(0, off - span)
    hi = min(len(da), off + span)
    print(f"leaf {path} len retail={len(da)} build={len(db)}  window {lo}..{hi}")
    print("retail:", da[lo:hi].hex(" "))
    print("build :", db[lo:hi].hex(" "))
    diff = [i for i in range(lo, min(hi, len(db))) if da[i] != db[i]]
    print("differing offsets in window:", diff)


if __name__ == "__main__":
    main()
