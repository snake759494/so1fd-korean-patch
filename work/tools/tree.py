"""Parse a so1pack member into a container tree and serialise it back.

Rebuild strategy: never re-author a container header.  A container keeps its
original bytes and each child is written back into the exact byte slot it came
from (zero-padded if it got shorter, rejected if it got longer).  That keeps
offset tables, header padding and entries that the parsers skip byte-identical
- the black-screen regression came from re-authoring those.

SLZ containers keep their per-member decoded sizes and their chain links; a
member whose mode this module cannot encode (1 and 3) is re-emitted as mode 0
(stored), which the game also uses natively, and mode 1/3 payloads are tried as
mode 2 first so the result still fits the original slot.

Node kinds:
  raw       leaf bytes
  slz       one SLZ container (possibly a chain) wrapping a child
  archive   [u32 count][u32 offsets[count]] + payload
  offtable  [u32 offsets...] where offsets[0] is the table size
  typed     [u32 count][(u32 type, u32 offset) * count] + payload  (field maps)
"""
from __future__ import annotations

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slz
from expand import as_archive, as_offset_table, as_typed_chunks


class Overflow(Exception):
    """A rebuilt child no longer fits the byte slot it came from."""


class Node:
    __slots__ = ("kind", "data", "kids", "slots", "path", "dirty")

    def __init__(self, kind, data=None, kids=None, slots=None, path=""):
        self.kind = kind
        self.data = data
        self.kids = kids or []
        self.slots = slots or []      # (start, end) of each kid inside self.data
        self.path = path
        self.dirty = False

    def __repr__(self):
        return f"<{self.kind} {self.path} kids={len(self.kids)} len={len(self.data or b'')}>"


def parse(d: bytes, path="", depth=0, maxdepth=6) -> Node:
    if depth > maxdepth or not d:
        return Node("raw", d, path=path)
    if slz.is_slz(d):
        try:
            inner = slz.decompress(d)
            return Node("slz", d, [parse(inner, path + "!", depth + 1, maxdepth)],
                        path=path)
        except Exception:
            pass
    typed = as_typed_chunks(d)
    if typed:
        parts, types = typed
        kids = [parse(d[a:b], f"{path}/t{types[k]}", depth + 1, maxdepth)
                for k, (a, b) in enumerate(parts)]
        return Node("typed", d, kids, parts, path)
    parts = as_archive(d)
    if parts and len(parts) > 1:
        kids = [parse(d[a:b], f"{path}/{k}", depth + 1, maxdepth)
                for k, (a, b) in enumerate(parts)]
        return Node("archive", d, kids, parts, path)
    parts = as_offset_table(d)
    if parts and len(parts) > 1:
        kids = [parse(d[a:b], f"{path}/{k}", depth + 1, maxdepth)
                for k, (a, b) in enumerate(parts)]
        return Node("offtable", d, kids, parts, path)
    return Node("raw", d, path=path)


def build(n: Node) -> bytes:
    if not n.dirty and n.data is not None:
        return n.data                     # untouched subtree: reuse verbatim
    if n.kind == "raw":
        return n.data
    if n.kind == "slz":
        inner = build(n.kids[0])
        try:
            out = slz.recompress_like(n.data, inner, limit=len(n.data))
        except ValueError as e:
            raise Overflow(f"{n.path}: {e}") from None
        if len(out) > len(n.data):
            raise Overflow(f"{n.path}: slz {len(out)} > {len(n.data)}")
        # keep whatever followed the container inside this slot instead of
        # zeroing it - the slack is not always padding
        buf = bytearray(n.data)
        buf[:len(out)] = out
        return bytes(buf)
    buf = bytearray(n.data)
    for kid, (a, b) in zip(n.kids, n.slots):
        body = build(kid)
        if len(body) > b - a:
            raise Overflow(f"{kid.path}: {len(body)} > slot {b - a}")
        buf[a:a + len(body)] = body
        if len(body) < b - a:
            buf[a + len(body):b] = b"\x00" * (b - a - len(body))
    return bytes(buf)


def walk(n: Node):
    yield n
    for k in n.kids:
        yield from walk(k)


def find(n: Node, path: str) -> Node | None:
    for x in walk(n):
        if x.path == path:
            return x
    return None


def mark(root: Node, path: str, data: bytes) -> bool:
    """Replace a leaf's bytes and mark the path to it dirty."""
    chain = []

    def visit(n):
        chain.append(n)
        if n.path == path:
            return True
        for k in n.kids:
            if visit(k):
                return True
        chain.pop()
        return False

    if not visit(root):
        return False
    chain[-1].data = data
    for x in chain:
        x.dirty = True
    return True


if __name__ == "__main__":
    from expand import load
    ok = bad = 0
    for a in sys.argv[1:] or [str(i) for i in range(0, 200)]:
        i = int(a)
        d = load(i)
        if not d:
            continue
        t = parse(d, str(i))
        for n in walk(t):
            n.dirty = True                # force the full rebuild path
        try:
            out = build(t)
        except Overflow as e:
            print("OVERFLOW", i, e)
            bad += 1
            continue
        if out == d:
            ok += 1
        else:
            bad += 1
            print("MISMATCH", i, len(d), len(out))
    print("forced-rebuild round-trip ok", ok, "bad", bad)
