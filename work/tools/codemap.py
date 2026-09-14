"""Message code -> font glyph index.

Some banks address the font in 128-glyph pages while the in-code offset field
is 8 bits wide, so every other 128-slot window is unused and the real index is

    index = slot - 128 * (slot // 256)

Other banks (the field-map t1 chunks) address the font flat.  Which of the two
a bank uses is decided by measuring how much kana each mapping yields.
"""
from __future__ import annotations

FLAT = "flat"
PAGED = "paged"


def to_index(slot: int, mode: str) -> int:
    return slot if mode == FLAT else slot - 128 * (slot // 256)


def to_slot(index: int, mode: str) -> int:
    if mode == FLAT:
        return index
    return index + 128 * max(0, index // 128 - 1)


def detect(slot_hist, ids, is_kana, count) -> str:
    """Pick the mapping that turns more of the used slots into kana."""
    score = {}
    for mode in (FLAT, PAGED):
        s = 0
        for slot, n in slot_hist.items():
            i = to_index(slot, mode)
            if 0 <= i < count and is_kana[ids[i]]:
                s += n
        score[mode] = s
    return FLAT if score[FLAT] >= score[PAGED] else PAGED
