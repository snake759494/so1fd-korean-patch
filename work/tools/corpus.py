"""Collect the unique Japanese strings, most frequent first.

The same fragment repeats across hundreds of banks, so translating by string
(not by occurrence) is what makes full coverage tractable.
"""
from __future__ import annotations

import io
import json
import re
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TSV = r"D:\psp\rom\SO1\work\text.tsv"
OUT = r"D:\psp\rom\SO1\work\corpus.tsv"
JP = re.compile(r"[\u3040-\u30FF\u4E00-\u9FFF]")
NOISE = {"5053"}


def load_rows():
    rows = []
    with io.open(TSV, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 7:
                continue
            if p[0].split("/")[0] in NOISE:
                continue
            rows.append(p)
    return rows


def is_text(s: str) -> bool:
    n = len(s)
    if n < 2 or "\ue000" in s:
        return False
    jp = len(JP.findall(s))
    return jp >= 2 and jp / n >= 0.5


def main():
    rows = load_rows()
    freq = Counter()
    for r in rows:
        if is_text(r[6]):
            freq[r[6]] += 1
    total_occ = sum(freq.values())
    print(f"unique strings {len(freq)}  occurrences {total_occ}")
    acc = 0
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("count\tcum%\tlen\ttext\n")
        for s, c in freq.most_common():
            acc += c
            f.write(f"{c}\t{acc / total_occ * 100:.1f}\t{len(s)}\t{s}\n")
    for k in (200, 500, 1000, 2000, 4000):
        acc = sum(c for _, c in freq.most_common(k))
        print(f"  top {k:>5} strings cover {acc / total_occ * 100:.1f}% of occurrences")


if __name__ == "__main__":
    main()
