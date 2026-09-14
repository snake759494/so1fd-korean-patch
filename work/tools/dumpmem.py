import os
import sys

OUT = r"D:\psp\rom\SO1\work\unpack"


def load(i):
    return open(os.path.join(OUT, "%02d" % (i // 500), "%05d.bin" % i), "rb").read()


i = int(sys.argv[1])
off = int(sys.argv[2], 0)
n = int(sys.argv[3], 0) if len(sys.argv) > 3 else 256
d = load(i)[off:off + n]
for j in range(0, len(d), 16):
    row = d[j:j + 16]
    print(f"{off + j:06X}  " + " ".join(f"{b:02X}" for b in row).ljust(47) + "  " +
          "".join(chr(b) if 32 <= b < 127 else "." for b in row))
