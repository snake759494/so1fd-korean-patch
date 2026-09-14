import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gim

OUT = r"D:\psp\rom\SO1\work\unpack"
DST = r"D:\psp\rom\SO1\work\gim_png"
os.makedirs(DST, exist_ok=True)

manifest = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
n = 0
for rec in manifest:
    i = rec["idx"]
    path = os.path.join(OUT, "%02d" % (i // 500), "%05d.bin" % i)
    d = open(path, "rb").read()
    if d[:12] != b"MIG.00.1PSP\x00":
        continue
    try:
        imgs, pals = gim.parse(d)
        img = gim.to_image(d)
    except Exception as e:
        print(i, "ERR", e)
        continue
    if img is None:
        print(i, "no image")
        continue
    info = imgs[0]
    img.save(os.path.join(DST, f"{i:05d}_{info['w']}x{info['h']}_{info['fmt_name']}.png"))
    n += 1
    print(f"{i:5d} {info['w']}x{info['h']} {info['fmt_name']} order={info['order']}")
print("saved", n)
