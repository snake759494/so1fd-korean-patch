"""Locate genuine Shift-JIS Japanese text inside the unpacked so1pack members.

Random binary decodes as rare kanji all the time, so a run only counts when it
is dominated by kana / ASCII / common punctuation.
"""
from __future__ import annotations

import json
import os
import re
import sys

OUT = r"D:\psp\rom\SO1\work\unpack"

KANA = re.compile(r"[\u3040-\u30FF]")
JP_OK = re.compile(r"[\u3040-\u30FF\u3000-\u303F\uFF00-\uFF9F\u4E00-\u9FFF\u0020-\u007E]")


def decode_runs(data: bytes, min_len: int = 6):
    """Yield (offset, text) for maximal SJIS-decodable byte runs."""
    n = len(data)
    i = 0
    while i < n:
        b = data[i]
        ok = (0x20 <= b <= 0x7E) or (0xA1 <= b <= 0xDF)
        dbl = (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF) and i + 1 < n and \
              (0x40 <= data[i + 1] <= 0xFC) and data[i + 1] != 0x7F
        if not (ok or dbl):
            i += 1
            continue
        start = i
        while i < n:
            b = data[i]
            if (0x20 <= b <= 0x7E) or (0xA1 <= b <= 0xDF):
                i += 1
            elif (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF) and i + 1 < n and \
                 (0x40 <= data[i + 1] <= 0xFC) and data[i + 1] != 0x7F:
                i += 2
            else:
                break
        if i - start >= min_len:
            try:
                txt = data[start:i].decode("cp932")
            except Exception:
                continue
            yield start, txt


def jp_score(txt: str):
    kana = len(KANA.findall(txt))
    good = len(JP_OK.findall(txt))
    return kana, good / max(1, len(txt))


def scan(data: bytes):
    """Return (n_jp_runs, samples) where a run must be kana-bearing and clean."""
    hits = []
    for off, txt in decode_runs(data):
        kana, ratio = jp_score(txt)
        if kana >= 3 and ratio > 0.95 and len(txt) >= 4:
            hits.append((off, txt))
    return hits


def main():
    manifest = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
    rows = []
    for rec in manifest:
        i = rec["idx"]
        path = os.path.join(OUT, "%02d" % (i // 500), "%05d.bin" % i)
        try:
            data = open(path, "rb").read()
        except FileNotFoundError:
            continue
        if not data:
            continue
        hits = scan(data)
        if hits:
            rows.append({"idx": i, "len": len(data), "sig": rec.get("sig"),
                         "dec_sig": rec.get("dec_sig"), "runs": len(hits),
                         "chars": sum(len(t) for _, t in hits),
                         "samples": [t[:40] for _, t in hits[:4]]})
    rows.sort(key=lambda r: -r["chars"])
    print("members with Japanese text:", len(rows),
          " total chars:", sum(r["chars"] for r in rows))
    for r in rows[:70]:
        print(f"  idx={r['idx']:<6} len={r['len']:<9} sig={r['sig']:<14} "
              f"dec={str(r['dec_sig']):<14} runs={r['runs']:<5} chars={r['chars']:<7} "
              + " | ".join(r["samples"][:3]))
    with open(r"D:\psp\rom\SO1\work\sjis_hits.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
