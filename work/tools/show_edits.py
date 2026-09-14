"""Show what the dictionary patch does to one member, in context.

For each edit it prints the surrounding decoded text plus the raw bytes just
before and after the span, so a misaligned run (an edit landing on opcode
bytes rather than on message text) is visible.
"""
from __future__ import annotations

import json
import pickle
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from so1pack import Pack
import codemap
import tree
from autopatch import load_rows, match_spans, shell_depth

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"


def main():
    member = int(sys.argv[1])
    dic = json.load(open(r"D:\psp\rom\SO1\work\dict.json", encoding="utf-8"))
    keys = sorted((k for k in dic if dic[k]), key=len, reverse=True)
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    label = inv.get("label") or inv["canon"]
    key, count = inv["member_font"][member]
    fi = cat[key]
    ids = inv["banks"][key]["ids"]

    rows = [r for r in load_rows() if int(r["path"].split("/")[0]) == member]
    pack = Pack()
    root = tree.parse(pack.read(member), str(member))
    k = shell_depth(root)
    pre = str(member)
    leaves = {}
    for n in tree.walk(root):
        p = n.path
        if p.startswith(pre + "!" * k):
            p = pre + p[len(pre) + k:]
        leaves[p] = n
    mode = rows[0]["mode"] if rows else "paged"

    def dec(buf, off, n):
        out = []
        for j in range(n):
            a = off + j * 2
            if a + 1 >= len(buf):
                break
            gi = codemap.to_index((buf[a] | (buf[a + 1] << 8)) - 0x101, mode)
            ch = label.get(ids[gi]) if 0 <= gi < count else None
            out.append(ch if ch else "\uFFFD")
        return "".join(out)

    shown = 0
    for r in rows:
        n = leaves.get(r["path"])
        if n is None or n.data is None:
            continue
        spans = match_spans(r["text"], keys)
        if not spans:
            continue
        buf = n.data
        a0 = r["off"]
        a1 = r["off"] + r["len"] * 2
        before = buf[max(0, a0 - 8):a0]
        after = buf[a1:a1 + 8]
        print(f"--- {r['path']} off={a0} len={r['len']}")
        print(f"    text : {r['text']}")
        print(f"    bytes: [{before.hex(' ')}] ... [{after.hex(' ')}]")
        for pos, kk in spans:
            print(f"    edit @{pos} {kk!r} -> {dic[kk]!r}"
                  f"   raw={buf[a0 + pos * 2:a0 + (pos + len(kk)) * 2].hex(' ')}")
        shown += 1
        if shown >= int(sys.argv[2] if len(sys.argv) > 2 else 12):
            break
    pack.close()


if __name__ == "__main__":
    main()
