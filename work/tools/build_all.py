"""so1pack.bin -> patched ISO -> xdelta, plus a verification pass."""
from __future__ import annotations

import hashlib
import os
import pickle
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repack_inplace import build
from build_iso import patch, SRC

BUILD = r"D:\psp\rom\SO1\work\build"
OUT_ISO = os.path.join(BUILD, "SO1_Korean.iso")
XDELTA = r"D:\psp\rom\SO1\xdelta.exe"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    # optional tag makes a side-by-side diagnostic build instead of the release
    tag = sys.argv[1] if len(sys.argv) > 1 else ""
    suffix = ("_" + tag) if tag else ""
    out_iso = os.path.join(BUILD, f"SO1_Korean{suffix}.iso")
    ov = pickle.load(open(os.path.join(BUILD, "overrides.pkl"), "rb"))
    print("overrides:", len(ov), "members")
    pack = build(ov, os.path.join(BUILD, f"so1pack{suffix}.bin"))
    print("so1pack:", os.path.getsize(pack), "bytes")
    patch(SRC, out_iso, {"/PSP_GAME/USRDIR/so1pack.bin": open(pack, "rb").read()})
    print("iso sha256:", sha(out_iso))
    if tag:
        return
    delta = os.path.join(BUILD, "SO1_Korean.xdelta")
    r = subprocess.run([XDELTA, "-e", "-f", "-s", SRC, out_iso, delta],
                       capture_output=True, text=True)
    print("xdelta rc", r.returncode, r.stderr.strip()[:200])
    if os.path.exists(delta):
        print("patch size:", os.path.getsize(delta), "bytes")


if __name__ == "__main__":
    main()
