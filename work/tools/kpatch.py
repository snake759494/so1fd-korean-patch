"""Apply Korean translations in place.

Spare glyph slots are repurposed for Hangul rendered from Galmuri11 12pt, then
the message codes are rewritten.  Every edit keeps the member's byte length
identical, so the so1pack and ISO layouts are untouched.
"""
from __future__ import annotations

import json
import pickle
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import load
from locate import locate
import codemap
import kfont

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"
TSV = r"D:\psp\rom\SO1\work\text.tsv"
BUILD = r"D:\psp\rom\SO1\work\build"
KEEP = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
           " 　･・?？!！)）]］>＞♪(（[［<＜『』=:;、,/-.%％")


def strings_of(member: int):
    out = []
    with open(TSV, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 7 and p[0].split("/")[0] == str(member):
                out.append({"path": p[0], "mode": p[2], "off": int(p[3]),
                            "len": int(p[4]), "text": p[6]})
    return out


def patch_member(member, items, inv, cat, report):
    d = bytearray(load(member))
    loc = locate(bytes(d), str(member))
    key, count = inv["member_font"][member]
    fi = cat[key]
    if fi["path"] not in loc:
        report.append((member, "font leaf not directly addressable"))
        return None
    fbase = loc[fi["path"]][0]
    wid_abs, bmp_abs = fbase + fi["widths"], fbase + fi["bitmaps"]
    ids = inv["banks"][key]["ids"]
    label = inv.get("label") or inv["canon"]

    all_str = strings_of(member)
    mode = all_str[0]["mode"] if all_str else codemap.PAGED
    todo = {(t["path"], int(t["off"])) for t in items}

    reserved = set()
    for s in all_str:
        if (s["path"], s["off"]) in todo:
            continue
        rng = loc.get(s["path"])
        if not rng:
            continue
        b0 = rng[0] + s["off"]
        for j in range(s["len"]):
            slot = (d[b0 + j * 2] | (d[b0 + j * 2 + 1] << 8)) - 0x101
            gi = codemap.to_index(slot, s["mode"])
            if 0 <= gi < count:
                reserved.add(gi)
    for gi in range(count):
        if label.get(ids[gi]) in KEEP:
            reserved.add(gi)

    need = Counter()
    for t in items:
        need.update(t["ko"])
    have = {}
    for gi in range(count):
        ch = label.get(ids[gi])
        if ch is not None and ch not in have:
            have[ch] = gi
    new_chars = [c for c in need if c not in have]
    free = [g for g in range(count) if g not in reserved]
    if len(new_chars) + 1 > len(free):
        report.append((member, f"need {len(new_chars)} slots, only {len(free)} free"))
        return None

    font = kfont._font()
    for ch, gi in zip(new_chars, free):
        bits = kfont.render(ch, font)
        d[bmp_abs + gi * 24: bmp_abs + gi * 24 + 24] = kfont.encode(bits)
        d[wid_abs + gi] = 12 if ord(ch) >= 0x1100 else kfont.advance(bits)
        have[ch] = gi
    space_gi = have.get(" ")
    if space_gi is None:
        space_gi = free[len(new_chars)]
        d[bmp_abs + space_gi * 24: bmp_abs + space_gi * 24 + 24] = b"\x00" * 24
        d[wid_abs + space_gi] = 4
        have[" "] = space_gi

    ok = 0
    for t in items:
        rng = loc.get(t["path"])
        if not rng:
            report.append((member, f"leaf {t['path']} not addressable"))
            continue
        base = rng[0] + int(t["off"])
        slots = int(t["len"])
        ko = t["ko"]
        if len(ko) > slots:
            report.append((member, f"'{ko}' needs {len(ko)} > {slots}"))
            continue
        seq = [have[c] for c in ko] + [space_gi] * (slots - len(ko))
        for j, gi in enumerate(seq):
            code = 0x101 + codemap.to_slot(gi, mode)
            d[base + j * 2] = code & 0xFF
            d[base + j * 2 + 1] = code >> 8
        ok += 1
    report.append((member, f"patched {ok}/{len(items)}, {len(new_chars)} new glyphs, "
                           f"{len(free)} free slots, mode={mode}"))
    return bytes(d)


def main():
    tr = json.load(open(sys.argv[1], encoding="utf-8"))
    by_member = {}
    for t in tr:
        by_member.setdefault(int(t["member"]), []).append(t)
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    out, report = {}, []
    for member, items in sorted(by_member.items()):
        res = patch_member(member, items, inv, cat, report)
        if res is not None:
            assert len(res) == len(load(member))
            out[member] = res
    for m, msg in report:
        print(f"  {m}: {msg}")
    os.makedirs(BUILD, exist_ok=True)
    pickle.dump(out, open(os.path.join(BUILD, "overrides.pkl"), "wb"))
    print("members patched:", len(out))


if __name__ == "__main__":
    main()
