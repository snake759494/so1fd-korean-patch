"""Contact sheet of PNGs in a directory."""
import os
import sys
from PIL import Image

src = sys.argv[1]
dst = sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
cell = int(sys.argv[4]) if len(sys.argv) > 4 else 220
files = sorted(f for f in os.listdir(src) if f.lower().endswith(".png"))
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell, rows * cell), (40, 40, 40))
for k, f in enumerate(files):
    im = Image.open(os.path.join(src, f)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("RGB")
    im.thumbnail((cell - 4, cell - 4))
    sheet.paste(im, ((k % cols) * cell + 2, (k // cols) * cell + 2))
sheet.save(dst)
print(dst, len(files))
