"""Dictionary-driven Korean patch over every bank.

Fragments are cut by script control codes, and a fragment's first/last unit is
sometimes a control byte pair that merely decodes as a glyph, so dictionary
keys are matched as substrings and only those spans are rewritten.

Members are edited through the container tree, so banks that live inside SLZ
(the field maps) can be patched too; untouched subtrees are copied verbatim so
only the edited chunk is re-compressed.
"""
from __future__ import annotations

import io
import json
import pickle
import sys
import os
import time
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expand import load
from so1pack import Pack
import codemap
import kfont
import tree


def shell_depth(root) -> int:
    """How many top-level SLZ wrappers `load()` already stripped."""
    n, k = root, 0
    while n.kind == "slz":
        k += 1
        n = n.kids[0]
    return k

INV = r"D:\psp\rom\SO1\work\glyphs.pkl"
CAT = r"D:\psp\rom\SO1\work\banks.json"
TSV = r"D:\psp\rom\SO1\work\text.tsv"
BUILD = r"D:\psp\rom\SO1\work\build"
KEEP = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
           " 　･・?？!！)）]］>＞♪(（[［<＜『』=:;、,/-.%％~^&*+_|")
NOISE = {"5053"}


def load_rows():
    rows = []
    with io.open(TSV, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 7 and p[0].split("/")[0] not in NOISE:
                rows.append({"path": p[0], "mode": p[2], "off": int(p[3]),
                             "len": int(p[4]), "text": p[6]})
    return rows


def match_spans(text, keys):
    n = len(text)
    used = [False] * n
    out = []
    for k in keys:
        start = 0
        while True:
            i = text.find(k, start)
            if i < 0:
                break
            if not any(used[i:i + len(k)]):
                for j in range(i, i + len(k)):
                    used[j] = True
                out.append((i, k))
            start = i + 1
    return out


def main():
    t0 = time.time()
    dic = json.load(open(sys.argv[1], encoding="utf-8"))
    # diagnostics: --font-only writes the Hangul glyphs but leaves every
    # message byte untouched; --members limits the patch to a member list
    font_only = "--font-only" in sys.argv
    # --null re-encodes exactly the same members with no content change at all,
    # so a failure can only come from the container rebuild itself
    null = "--null" in sys.argv
    font_only = font_only or null
    only = None
    if "--members" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--members") + 1].split(",")}
    keys = sorted((k for k in dic if dic[k]), key=len, reverse=True)
    inv = pickle.load(open(INV, "rb"))
    cat = {r["key"]: r for r in json.load(open(CAT))}
    label = inv.get("label") or inv["canon"]
    rows = load_rows()
    by_member = defaultdict(list)
    for r in rows:
        by_member[int(r["path"].split("/")[0])].append(r)

    pack = Pack()
    overrides = {}
    stats = Counter()
    font = kfont._font()
    for member, rs in sorted(by_member.items()):
        if member not in inv["member_font"]:
            continue
        if only is not None and member not in only:
            continue
        key, count = inv["member_font"][member]
        fi = cat[key]

        # parse the *stored* member so the rebuild lands back in its byte slot;
        # text.tsv paths were made from the already-decompressed view, so the
        # top-level SLZ shells have to be spliced out of the path names
        root = tree.parse(pack.read(member), str(member))
        pre = str(member)
        k = shell_depth(root)

        def to_tsv(path, _p=pre, _k=k):
            return _p + path[len(_p) + _k:] if path.startswith(_p + "!" * _k) else path

        def to_tree(path, _p=pre, _k=k):
            return _p + "!" * _k + path[len(_p):]

        # Leaves only, keyed by their real tree path.  Container bytes are just
        # their children's bytes seen again, and stripping the SLZ marks off a
        # path can make two different leaves collide under one name - either
        # way a leaf would drop out of the scan while its glyph references
        # stayed alive on screen.
        leaves = {n.path: n for n in tree.walk(root) if n.data and not n.kids}
        fnode = leaves.get(to_tree(fi["path"]))
        if fnode is None or fnode.data is None:
            stats["no_font_leaf"] += 1
            continue
        wid_abs, bmp_abs = fi["widths"], fi["bitmaps"]
        ids = inv["banks"][key]["ids"]
        mode = rs[0]["mode"]

        bufs = {p: bytearray(n.data) for p, n in leaves.items() if n.data}
        fpath = to_tree(fi["path"])
        if fpath not in bufs:
            bufs[fpath] = bytearray(fnode.data)
        fbuf = bufs[fpath]

        def in_font(path, a, nbytes):
            return path == fpath and a + nbytes > fi["hdr"] and a < fi["end"]

        # Find the dictionary words by their glyph codes across the whole
        # member rather than inside detected runs.  Run detection only sees a
        # fraction of the text, and a word we miss keeps its glyphs alive - so
        # searching the raw bytes is both what frees the slots and what makes
        # freeing them safe.
        ch2gi = {}
        for gi in range(count):
            c = label.get(ids[gi])
            if c is not None and c not in ch2gi:
                ch2gi[c] = gi

        def pattern(word):
            out = bytearray()
            for c in word:
                code = 0x101 + codemap.to_slot(ch2gi[c], mode)
                out += bytes((code & 0xFF, code >> 8))
            return bytes(out)

        edits = []
        taken = {p: np.zeros(len(b), dtype=bool) for p, b in bufs.items()}
        for kk in keys:
            ko = dic[kk]
            if len(ko) > len(kk):
                stats["too_long"] += 1
                continue
            if any(c not in ch2gi for c in kk):
                continue
            pat = pattern(kk)
            n = len(pat)
            for path, buf in bufs.items():
                hay = bytes(buf)
                i = hay.find(pat)
                while i >= 0:
                    if not in_font(path, i, n) and not taken[path][i:i + n].any():
                        taken[path][i:i + n] = True
                        edits.append((path, i, len(kk), ko))
                    i = hay.find(pat, i + 1)
        if not edits:
            continue

        # Which glyphs are free?  Not "the ones our run detector never saw" -
        # that detector only accounts for 41% of the glyphs a bank carries, and
        # trusting it overwrote 6,866 live glyphs.  A bank holds exactly the
        # glyphs its map needs, so treat *every* byte pair anywhere in the
        # member that decodes to a valid glyph as a live reference.  A glyph is
        # free only when every one of its references sits inside the bytes this
        # patch is about to overwrite.  False positives merely protect a glyph,
        # which is the safe direction.
        # Every byte pair anywhere in the member that decodes to a valid glyph
        # counts as a live reference - run detection only sees 41% of the text,
        # and trusting it overwrote 6,866 live glyphs.  False positives merely
        # protect a glyph, which is the safe direction.
        refs = {}
        for path, node in leaves.items():
            b = node.data
            if not b or len(b) < 2:
                continue
            arr = np.frombuffer(b, dtype=np.uint8).astype(np.int32)
            slot = (arr[:-1] | (arr[1:] << 8)) - 0x101
            idx = slot if mode == codemap.FLAT else slot - 128 * (slot // 256)
            live = (idx >= 0) & (idx < count) & (slot >= 0)
            if path == fpath:                 # glyph bitmaps are not references
                live[max(0, fi["hdr"] - 1): fi["end"]] = False
            off = np.flatnonzero(live)
            refs[path] = (off, idx[off])

        base_have = {}
        for gi in range(count):
            ch = label.get(ids[gi])
            if ch is not None and ch not in base_have:
                base_have[ch] = gi
        keep = {gi for gi in range(count) if label.get(ids[gi]) in KEEP}

        # A glyph is free only if every reference to it dies in this patch, but
        # an edit only happens if its glyphs are free - a circular condition.
        # Solve it by shrinking the accepted set until it is consistent: an
        # edit we end up skipping must not have counted towards freeing a slot,
        # or its old character would still be on screen wearing a new shape.
        accepted = edits
        converged = False
        for _ in range(8):
            touch = {p: np.zeros(len(b), dtype=bool) for p, b in bufs.items()}
            for path, base, klen, ko in accepted:
                touch[path][base: base + klen * 2] = True
            reserved = set(keep)
            for path, (off, gidx) in refs.items():
                t = touch.get(path)
                alive = ~(t[off] & t[off + 1]) if t is not None else np.ones(off.size, bool)
                if alive.any():
                    reserved.update(np.unique(gidx[alive]).tolist())
            need = Counter()
            for _p, _b, klen, ko in accepted:
                need.update(ko)
                if len(ko) < klen:
                    need[" "] += 1
            new_chars = [c for c, _ in need.most_common() if c not in base_have]
            free = [g for g in range(count) if g not in reserved]
            plan = dict(zip(new_chars, free))
            have = dict(base_have)
            have.update(plan)
            ok = [e for e in accepted
                  if all(c in have for c in e[3])
                  and (len(e[3]) == e[2] or " " in have)]
            if len(ok) == len(accepted):
                converged = True
                break
            stats["missing_glyph"] += len(accepted) - len(ok)
            accepted = ok
            if not accepted:
                break
        if not accepted or not converged:
            # an unconverged plan would free slots for edits we then skip
            stats["slot_short" if accepted else "no_slots"] += 1
            continue

        wid_lo = fi["hdr"] + 8          # never write over the u32 height field
        for ch, gi in (() if null else plan.items()):
            if ch == " ":
                fbuf[bmp_abs + gi * 24: bmp_abs + gi * 24 + 24] = b"\x00" * 24
                if wid_abs + gi >= wid_lo:
                    fbuf[wid_abs + gi] = 4
                continue
            bits = kfont.render(ch, font)
            fbuf[bmp_abs + gi * 24: bmp_abs + gi * 24 + 24] = kfont.encode(bits)
            if wid_abs + gi >= wid_lo:
                fbuf[wid_abs + gi] = 12 if ord(ch) >= 0x1100 else kfont.advance(bits)
        space_gi = have.get(" ")

        applied = 0
        for path, base, klen, ko in accepted:
            if font_only:
                break          # glyphs go in, message bytes stay untouched
            b = bufs[path]
            seq = [have[c] for c in ko] + [space_gi] * (klen - len(ko))
            for j, gi in enumerate(seq):
                code = 0x101 + codemap.to_slot(gi, mode)
                b[base + j * 2] = code & 0xFF
                b[base + j * 2 + 1] = code >> 8
            applied += 1
        if not applied and not font_only:
            continue

        # Final guard, and the only one that measures what a player sees: a
        # glyph whose bitmap we replaced must not still be pointed at by bytes
        # we did not write, or that character renders as the wrong letter.
        # The reference bookkeeping above is meant to make this impossible;
        # it has been wrong before, so check the actual result and drop the
        # member rather than ship corrupted text.
        placed = set(plan.values())
        if placed:
            dirty = False
            for path, buf in bufs.items():
                orig = leaves[path].data
                if len(orig) != len(buf) or len(orig) < 2:
                    continue
                x = np.frombuffer(orig, dtype=np.uint8).astype(np.int32)
                y = np.frombuffer(bytes(buf), dtype=np.uint8).astype(np.int32)
                s = (y[:-1] | (y[1:] << 8)) - 0x101
                i2 = s if mode == codemap.FLAT else s - 128 * (s // 256)
                m = (s >= 0) & (i2 >= 0) & (i2 < count)
                m &= (x[:-1] == y[:-1]) & (x[1:] == y[1:])
                if path == fpath:
                    m[max(0, fi["hdr"] - 1): fi["end"]] = False
                if m.any() and placed.intersection(np.unique(i2[m]).tolist()):
                    dirty = True
                    break
            if dirty:
                stats["contaminated"] += 1
                continue

        for path, buf in bufs.items():
            tree.mark(root, path, bytes(buf))
        try:
            overrides[member] = tree.build(root)
        except tree.Overflow as e:
            stats["overflow"] += 1
            continue
        stats["members"] += 1
        stats["edits"] += applied
        if stats["members"] % 100 == 0:
            print(f"  .. {stats['members']} members, {time.time() - t0:.0f}s", flush=True)

    os.makedirs(BUILD, exist_ok=True)
    pickle.dump(overrides, open(os.path.join(BUILD, "overrides.pkl"), "wb"))
    print("dictionary entries:", len(keys))
    print("patched members:", stats["members"], " edits:", stats["edits"],
          f" elapsed {time.time() - t0:.0f}s")
    pack.close()
    for k in ("too_long", "slot_short", "missing_glyph", "no_space_slot",
              "no_font_leaf", "overflow", "contaminated", "no_slots"):
        if stats[k]:
            print(f"  {k}: {stats[k]}")


if __name__ == "__main__":
    main()
