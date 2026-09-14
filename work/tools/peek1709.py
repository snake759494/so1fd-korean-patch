"""What text does the one bank with spare glyph slots actually carry?"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autopatch import load_rows


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else "1709"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    rows = [r for r in load_rows() if r["path"].split("/")[0] == want]
    print(f"rows in member {want}: {len(rows)}")
    print("total chars:", sum(len(r["text"]) for r in rows))
    rows.sort(key=lambda r: -len(r["text"]))
    for r in rows[:n]:
        print(f"  {r['path']} off={r['off']:6d} len={r['len']:3d}  {r['text']}")


if __name__ == "__main__":
    main()
