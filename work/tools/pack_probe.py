import struct
import sys
import os

path = r"D:\psp\rom\SO1\work\extract\PSP_GAME\USRDIR\so1pack.bin"
f = open(path, "rb")
fsize = os.path.getsize(path)
hdr0 = struct.unpack("<I", f.read(4))[0]
f.seek(0)
toc = f.read(hdr0)
vals = struct.unpack("<%dI" % (len(toc) // 4), toc)

breaks = [i for i in range(1, len(vals) - 1) if vals[i] > vals[i + 1]]
print("monotonic breaks at indices:", breaks[:20], "total", len(breaks))
for i in breaks[:10]:
    print(f"  i={i}: {hex(vals[i-1])} {hex(vals[i])} -> {hex(vals[i+1])} {hex(vals[i+2])}")

zeros = [i for i, v in enumerate(vals) if v == 0]
print("zero entries:", len(zeros), zeros[:20])

# dump data at a few offsets (raw byte interpretation)
def hexdump(off, n=64, label=""):
    f.seek(off)
    d = f.read(n)
    print(f"--- {label} @ {hex(off)}")
    for i in range(0, len(d), 16):
        row = d[i:i+16]
        print(f"  {off+i:08X}  " + " ".join(f"{b:02X}" for b in row).ljust(47) + "  " +
              "".join(chr(b) if 32 <= b < 127 else "." for b in row))

for idx in (1, 2, 3, 5, 10):
    hexdump(vals[idx], 64, f"vals[{idx}] as byte off")
    hexdump(vals[idx] * 0x800, 64, f"vals[{idx}]*0x800")
